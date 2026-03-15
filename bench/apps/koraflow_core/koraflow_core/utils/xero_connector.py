import frappe
from frappe import _
from xero_python.identity import IdentityApi
from xero_python.accounting import AccountingApi
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from datetime import datetime, timedelta
import os
import time
import requests
import base64

class XeroConnector:
    def __init__(self):
        self.settings = frappe.get_single("Xero Settings")
        self.client_id = self.settings.client_id
        self.client_secret = self.settings.get_password("client_secret")
        self.redirect_uri = self.settings.redirect_uri
        self.scope = "offline_access accounting.transactions accounting.contacts"

        def oauth2_token_getter():
            expires_in = 1800 # Default fallback
            if self.settings.token_expiry:
                expiry = self.settings.token_expiry
                if isinstance(expiry, str):
                    from frappe.utils import get_datetime
                    expiry = get_datetime(expiry)
                
                # Calculate seconds remaining
                delta = expiry - datetime.now()
                expires_in = int(delta.total_seconds())

            return {
                "access_token": self.settings.access_token,
                "refresh_token": self.settings.refresh_token,
                "token_type": "Bearer",
                "scope": self.scope,
                "expires_in": expires_in
            }

        self.api_client = ApiClient(
            Configuration(
                debug=False,
                oauth2_token=OAuth2Token(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                ),
            ),
            pool_threads=1,
            oauth2_token_getter=oauth2_token_getter
        )

    def get_authorization_url(self):
        if not self.client_id or not self.client_secret:
            frappe.throw(_("Please configure Client ID and Secret in Xero Settings"))
        
        # Manual URL construction
        base_url = "https://login.xero.com/identity/connect/authorize"
        params = [
            f"response_type=code",
            f"client_id={self.client_id}",
            f"redirect_uri={self.redirect_uri}",
            f"scope={self.scope}",
            f"state={frappe.generate_hash()}"
        ]
        return f"{base_url}?{'&'.join(params)}"
    
    def callback(self, state, code):
        try:
            # Exchange code for token
            token_url = "https://identity.xero.com/connect/token"
            
            # Auth header
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            res = requests.post(token_url, headers=headers, data=data)
            
            if res.status_code != 200:
                msg = f"Xero Token Exchange Failed: {res.text}"
                frappe.log_error(title="Xero Connector", message=msg)
                return False, msg
                
            token = res.json()
            self.save_token(token)
            self.set_tenant_id()
            return True, None
        except Exception as e:
            msg = f"Xero Callback Error: {str(e)}"
            frappe.log_error(title="Xero Callback Error", message=msg)
            return False, msg

    def save_token(self, token):
        if not token:
            return
            
        self.settings.access_token = token.get("access_token")
        self.settings.refresh_token = token.get("refresh_token")
        
        if token.get("expires_in"):
            expiry = datetime.now() + timedelta(seconds=token.get("expires_in"))
            self.settings.token_expiry = expiry

        self.settings.save()
        frappe.db.commit()

    def set_tenant_id(self):
        self.refresh_access_token_if_needed()
        
        # Ensure token is set on client for Identity API calls
        self.api_client.configuration.oauth2_token.access_token = self.settings.access_token
        
        identity_api = IdentityApi(self.api_client)
        connections = identity_api.get_connections()
        
        if connections and len(connections) > 0:
            self.settings.tenant_id = connections[0].tenant_id
            self.settings.connection_status = "Connected"
            self.settings.save()
            frappe.db.commit()
        else:
            frappe.msgprint("No Xero Tenants found for this connection.")

    def refresh_access_token_if_needed(self):
        if not self.settings.refresh_token:
             return

        should_refresh = False
        if not self.settings.token_expiry:
             should_refresh = True
        else:
             expiry = self.settings.token_expiry
             if isinstance(expiry, str):
                 from frappe.utils import get_datetime
                 expiry = get_datetime(expiry)
             
             if expiry < datetime.now() + timedelta(minutes=5):
                 should_refresh = True

        if should_refresh:
            try:
                token_url = "https://identity.xero.com/connect/token"
                auth_str = f"{self.client_id}:{self.client_secret}"
                auth_b64 = base64.b64encode(auth_str.encode()).decode()
                
                headers = {
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.settings.refresh_token
                }
                
                res = requests.post(token_url, headers=headers, data=data)
                if res.status_code != 200:
                    raise Exception(f"Refresh failed: {res.text}")
                    
                new_token = res.json()
                self.save_token(new_token)
            except Exception as e:
                frappe.log_error(title="Xero Token Refresh", message=f"Xero Token Refresh Failed: {str(e)}")
                self.settings.connection_status = "Disconnected (Refresh Failed)"
                self.settings.save()

    def get_accounting_api(self):
        self.refresh_access_token_if_needed()
        # Ensure fresh token is in config
        self.api_client.configuration.oauth2_token.access_token = self.settings.access_token
        return AccountingApi(self.api_client)

    def get_or_create_contact(self, customer_name):
        api = self.get_accounting_api()
        # Check if contact exists
        where = f'Name=="{customer_name}"'
        try:
            contacts = api.get_contacts(self.settings.tenant_id, where=where)
            if contacts.contacts:
                return contacts.contacts[0].contact_id
            
            # Create
            contact = {"Name": customer_name}
            created = api.create_contacts(self.settings.tenant_id, contacts=contact)
            return created.contacts[0].contact_id
        except Exception as e:
            frappe.throw(f"Error syncing contact {customer_name}: {str(e)}")

    def create_quote(self, doc):
        api = self.get_accounting_api()
        contact_id = self.get_or_create_contact(doc.customer_name)
        
        line_items = []
        for item in doc.items:
            line_items.append({
                "Description": item.description or item.item_name,
                "Quantity": item.qty,
                "UnitAmount": item.rate,
                "ItemCode": item.item_code,
                "AccountCode": self.settings.default_sales_account or "200" # Default 200 (Sales)
            })
            
        quote_data = {
            "Contact": {"ContactID": contact_id},
            "Date": str(doc.transaction_date),
            "LineItems": line_items,
            "QuoteNumber": doc.name,
            "Reference": doc.name,
            "Status": "SENT" # Or DRAFT
        }
        
        try:
            res = api.create_quotes(self.settings.tenant_id, quotes={"Quotes": [quote_data]})
            if res.quotes:
                frappe.msgprint(_("Synced Quote {} to Xero").format(doc.name))
        except Exception as e:
            raise e

    def create_invoice(self, doc):
        api = self.get_accounting_api()
        contact_id = self.get_or_create_contact(doc.customer_name)
        
        line_items = []
        for item in doc.items:
            line_items.append({
                "Description": item.description or item.item_name,
                "Quantity": item.qty,
                "UnitAmount": item.rate,
                "ItemCode": item.item_code,
                "AccountCode": self.settings.default_sales_account or "200" 
            })
            
        invoice_data = {
            "Type": "ACCREC",
            "Contact": {"ContactID": contact_id},
            "Date": str(doc.posting_date),
            "DueDate": str(doc.due_date),
            "LineItems": line_items,
            "InvoiceNumber": doc.name,
            "Reference": doc.name,
            "Status": "AUTHORISED"
        }
        
        try:
            res = api.create_invoices(self.settings.tenant_id, invoices={"Invoices": [invoice_data]})
            if res.invoices:
                frappe.msgprint(_("Synced Invoice {} to Xero").format(doc.name))
        except Exception as e:
            raise e

    def sync_xero_payments(self):
        """
        Fetches recent payments from Xero and creates Payment Entries in Frappe.
        """
        api = self.get_accounting_api()
        try:
             # get_payments(xero_tenant_id, where=None, order=None, page=None)
             res = api.get_payments(self.settings.tenant_id, order="Date DESC")
             if not res.payments: return
             
             for payment in res.payments:
                 if payment.status == "AUTHORISED":
                     self.process_xero_payment(payment)
        except Exception as e:
            frappe.log_error(title="Xero Payment Sync", message=f"Xero Payment Sync Error: {str(e)}")

    def process_xero_payment(self, payment):
        # payment.invoice has properties. If it is linked to an Invoice. 
        # Note: Xero Payment can link to Invoice or CreditNote.
        if not payment.invoice: return
        
        # The 'invoice' object in payment list might only have ID. 
        # We need the Invoice Number to match Frappe.
        if not payment.invoice.invoice_number:
            # Fetch invoice details if number missing
            api = self.get_accounting_api()
            inv_res = api.get_invoice(self.settings.tenant_id, payment.invoice.invoice_id)
            if not inv_res.invoices: return
            xero_inv = inv_res.invoices[0]
            invoice_number = xero_inv.invoice_number
        else:
            invoice_number = payment.invoice.invoice_number
            
        # Check if Invoice exists in Frappe
        if not frappe.db.exists("Sales Invoice", invoice_number):
            # Maybe it wasn't synced from Frappe, or renamed. Ignore.
            return
            
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_number)
        
        if invoice_doc.outstanding_amount <= 0:
            return
            
        # Create Payment Entry
        self.create_payment_entry(invoice_doc, payment.amount, payment.date)

    def create_payment_entry(self, invoice, amount, date):
        from frappe.utils import getdate
        
        if self.settings.default_payment_account:
            bank_account = self.settings.default_payment_account
        else:
            # Fallback to Company default
            company_doc = frappe.get_doc("Company", invoice.company)
            bank_account = company_doc.default_bank_account
            
        if not bank_account: # Fallback to first bank account
            accs = frappe.get_all("Account", filters={"account_type": "Bank", "company": invoice.company}, limit=1)
            if accs: bank_account = accs[0].name
            
        if not bank_account:
            frappe.log_error(title="Xero Payment Sync", message=f"No Bank Account found for Company {invoice.company}. Cannot sync Xero Payment.")
            return

        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.posting_date = getdate(date)
        pe.company = invoice.company
        pe.party_type = "Customer"
        pe.party = invoice.customer
        pe.paid_to = bank_account
        pe.paid_amount = amount
        pe.received_amount = amount
        pe.reference_no = invoice.name # Or Xero Payment ID?
        pe.reference_date = getdate(date)
        
        # Allocate to the invoice
        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "allocated_amount": amount
        })
        
        pe.save()
        pe.submit()
        frappe.msgprint(_("Created Payment Entry {} from Xero").format(pe.name))

# Helper function to get connector instance
def get_xero_connector():
    return XeroConnector()


# Event Handlers
def sync_quotation(doc, method=None):
    if doc.docstatus != 1: return
    try:
        connector = get_xero_connector()
        if not connector.settings.enable_xero: return
        connector.create_quote(doc)
    except Exception as e:
        frappe.log_error(title="Xero Quote Sync Error", message=frappe.get_traceback())
        frappe.msgprint(_("Failed to sync Quote to Xero: {}").format(str(e)), indicator='orange')

def sync_invoice(doc, method=None):
    if doc.docstatus != 1: return
    try:
        connector = get_xero_connector()
        if not connector.settings.enable_xero: return
        connector.create_invoice(doc)
    except Exception as e:
        frappe.log_error(title="Xero Invoice Sync Error", message=frappe.get_traceback())
        frappe.msgprint(_("Failed to sync Invoice to Xero: {}").format(str(e)), indicator='orange')

def sync_xero_payments():
    # Wrapper for scheduler
    try:
        connector = get_xero_connector()
        if connector.settings.enable_xero:
            connector.sync_xero_payments()
    except Exception as e:
        frappe.log_error(title="Xero Payment Sync", message=f"Scheduled Xero Payment Sync Error: {str(e)}")
