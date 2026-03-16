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
            token_url = "https://identity.xero.com/connect/token"
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
        self.api_client.configuration.oauth2_token.access_token = self.settings.access_token
        return AccountingApi(self.api_client)

    # =====================
    # Contact / Customer Sync
    # =====================

    def get_or_create_contact(self, customer_name, customer_doc=None):
        """Get or create a Xero contact for a customer.
        Uses custom_xero_contact_id for ID-based lookup first, falls back to name search.
        """
        api = self.get_accounting_api()

        # 1. Try ID-based lookup if we have a linked Customer doc
        if customer_doc and customer_doc.get("custom_xero_contact_id"):
            try:
                res = api.get_contact(self.settings.tenant_id, customer_doc.custom_xero_contact_id)
                if res.contacts:
                    return res.contacts[0].contact_id
            except Exception:
                pass  # Fall through to name search

        # 2. If customer_doc not passed, try to find it
        if not customer_doc:
            customer_name_clean = customer_name
            if frappe.db.exists("Customer", customer_name):
                customer_doc = frappe.get_doc("Customer", customer_name)
                if customer_doc.get("custom_xero_contact_id"):
                    try:
                        res = api.get_contact(self.settings.tenant_id, customer_doc.custom_xero_contact_id)
                        if res.contacts:
                            return res.contacts[0].contact_id
                    except Exception:
                        pass

        # 3. Name-based search in Xero
        where = f'Name=="{customer_name}"'
        try:
            contacts = api.get_contacts(self.settings.tenant_id, where=where)
            if contacts.contacts:
                contact_id = contacts.contacts[0].contact_id
                # Save the Xero ID back to Frappe Customer for future lookups
                self._save_xero_contact_id(customer_name, contact_id)
                return contact_id

            # 4. Create new contact in Xero
            contact_data = {"Name": customer_name}
            if customer_doc:
                email = customer_doc.get("email_id") or ""
                phone = customer_doc.get("mobile_no") or ""
                if email:
                    contact_data["EmailAddress"] = email
                if phone:
                    contact_data["Phones"] = [{"PhoneType": "MOBILE", "PhoneNumber": phone}]

            created = api.create_contacts(self.settings.tenant_id, contacts=contact_data)
            contact_id = created.contacts[0].contact_id
            # Save the Xero ID back to Frappe Customer
            self._save_xero_contact_id(customer_name, contact_id)
            return contact_id
        except Exception as e:
            frappe.throw(f"Error syncing contact {customer_name}: {str(e)}")

    def _save_xero_contact_id(self, customer_name, contact_id):
        """Save Xero Contact ID back to Frappe Customer record."""
        if frappe.db.exists("Customer", customer_name):
            frappe.db.set_value("Customer", customer_name, {
                "custom_xero_contact_id": contact_id,
                "custom_xero_sync_date": frappe.utils.now()
            })

    def sync_xero_contacts(self):
        """Pull contacts from Xero and create/update Customers in Frappe."""
        api = self.get_accounting_api()
        try:
            # Use modified_since for incremental sync
            modified_since = None
            if self.settings.get("last_contact_sync"):
                modified_since = self.settings.last_contact_sync
                if isinstance(modified_since, str):
                    from frappe.utils import get_datetime
                    modified_since = get_datetime(modified_since)

            kwargs = {"order": "Name ASC"}
            if modified_since:
                kwargs["if_modified_since"] = modified_since

            page = 1
            while True:
                res = api.get_contacts(self.settings.tenant_id, page=page, **kwargs)
                if not res.contacts:
                    break

                for contact in res.contacts:
                    self._import_xero_contact(contact)

                if len(res.contacts) < 100:
                    break
                page += 1

            # Update last sync timestamp
            self.settings.last_contact_sync = frappe.utils.now()
            self.settings.save()
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(title="Xero Contact Sync", message=f"Error syncing contacts from Xero: {str(e)}")

    def _import_xero_contact(self, xero_contact):
        """Import or update a single Xero contact as a Frappe Customer."""
        contact_id = xero_contact.contact_id
        contact_name = xero_contact.name

        if not contact_name:
            return

        # Check if already linked by Xero ID
        existing = frappe.db.get_value("Customer",
            {"custom_xero_contact_id": contact_id}, "name")

        if existing:
            # Update name if changed
            current_name = frappe.db.get_value("Customer", existing, "customer_name")
            if current_name != contact_name:
                frappe.db.set_value("Customer", existing, "customer_name", contact_name)
            return

        # Check if customer with same name exists (link it)
        existing_by_name = frappe.db.get_value("Customer",
            {"customer_name": contact_name}, "name")

        if existing_by_name:
            frappe.db.set_value("Customer", existing_by_name, {
                "custom_xero_contact_id": contact_id,
                "custom_xero_sync_date": frappe.utils.now()
            })
            return

        # Create new Customer from Xero contact
        try:
            customer = frappe.new_doc("Customer")
            customer.customer_name = contact_name
            customer.customer_type = "Individual"
            customer.customer_group = "Xero Customers"
            customer.territory = self._get_default_territory()
            customer.custom_xero_contact_id = contact_id
            customer.custom_is_xero_customer = 1
            customer.custom_xero_sync_date = frappe.utils.now()
            customer.custom_intake_required = 1
            customer.custom_intake_completed = 0

            # Extract email and phone from Xero contact
            if xero_contact.email_address:
                customer.email_id = xero_contact.email_address
            if xero_contact.phones:
                for phone in xero_contact.phones:
                    if phone.phone_number:
                        customer.mobile_no = phone.phone_number
                        break

            customer.flags.ignore_permissions = True
            customer.insert()
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(title="Xero Contact Import",
                message=f"Error importing Xero contact {contact_name}: {str(e)}")

    def _get_default_territory(self):
        """Get default territory for new customers."""
        default = frappe.db.get_single_value("Selling Settings", "territory") or "South Africa"
        if not frappe.db.exists("Territory", default):
            return frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"
        return default

    # =====================
    # Quote Sync
    # =====================

    def create_quote(self, doc):
        """Sync a Frappe Quotation to Xero. Saves Xero Quote ID back."""
        # Idempotency: skip if already synced
        if doc.get("custom_xero_quote_id"):
            return doc.custom_xero_quote_id

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

        quote_data = {
            "Contact": {"ContactID": contact_id},
            "Date": str(doc.transaction_date),
            "LineItems": line_items,
            "QuoteNumber": doc.name,
            "Reference": doc.name,
            "Status": "SENT"
        }

        try:
            res = api.create_quotes(self.settings.tenant_id, quotes={"Quotes": [quote_data]})
            if res.quotes:
                xero_quote_id = res.quotes[0].quote_id
                # Save Xero Quote ID back to Frappe
                frappe.db.set_value("Quotation", doc.name, "custom_xero_quote_id", xero_quote_id)
                frappe.db.commit()
                return xero_quote_id
        except Exception as e:
            raise e

    def sync_xero_quotes(self):
        """Pull quote status updates from Xero (hourly fallback to webhooks)."""
        api = self.get_accounting_api()
        try:
            # Only fetch quotes modified in last 2 hours
            since = datetime.now() - timedelta(hours=2)

            res = api.get_quotes(self.settings.tenant_id,
                if_modified_since=since, order="DateString DESC")

            if not res.quotes:
                return

            for xero_quote in res.quotes:
                self._process_xero_quote_status(xero_quote)

        except Exception as e:
            frappe.log_error(title="Xero Quote Sync",
                message=f"Error syncing quotes from Xero: {str(e)}")

    def _process_xero_quote_status(self, xero_quote):
        """Update Frappe Quotation status based on Xero quote status."""
        quote_number = xero_quote.quote_number
        if not quote_number:
            return

        # Find matching Frappe Quotation
        if not frappe.db.exists("Quotation", quote_number):
            # Try by Xero Quote ID
            frappe_quote = frappe.db.get_value("Quotation",
                {"custom_xero_quote_id": xero_quote.quote_id}, "name")
            if not frappe_quote:
                return
            quote_number = frappe_quote

        xero_status = xero_quote.status
        if xero_status == "ACCEPTED":
            # Xero quote was accepted - trigger acceptance flow in Frappe
            doc = frappe.get_doc("Quotation", quote_number)
            if doc.docstatus == 1 and doc.status != "Ordered":
                frappe.db.set_value("Quotation", quote_number, "status", "Open")
        elif xero_status == "DECLINED":
            doc = frappe.get_doc("Quotation", quote_number)
            if doc.docstatus == 1 and doc.status not in ("Lost", "Ordered"):
                frappe.db.set_value("Quotation", quote_number, "status", "Lost")

    # =====================
    # Invoice Sync
    # =====================

    def create_invoice(self, doc):
        """Sync a Frappe Sales Invoice to Xero. Saves Xero Invoice ID back."""
        # Idempotency: skip if already synced
        if doc.get("custom_xero_invoice_id"):
            return doc.custom_xero_invoice_id

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
                xero_invoice = res.invoices[0]
                xero_invoice_id = xero_invoice.invoice_id
                xero_invoice_number = getattr(xero_invoice, 'invoice_number', doc.name)
                # Save Xero Invoice ID and number back to Frappe
                frappe.db.set_value("Sales Invoice", doc.name, {
                    "custom_xero_invoice_id": xero_invoice_id,
                    "custom_xero_invoice_number": xero_invoice_number or doc.name,
                    "custom_xero_status": "AUTHORISED"
                })
                frappe.db.commit()
                return xero_invoice_id
        except Exception as e:
            raise e

    # =====================
    # Payment Sync (Xero → Frappe)
    # =====================

    def sync_xero_payments(self):
        """Fetches recent payments from Xero and creates Payment Entries in Frappe."""
        api = self.get_accounting_api()
        try:
            # Only fetch payments from the last 2 hours to avoid re-processing
            since = datetime.now() - timedelta(hours=2)
            res = api.get_payments(self.settings.tenant_id,
                order="Date DESC", if_modified_since=since)
            if not res.payments:
                return

            for payment in res.payments:
                if payment.status == "AUTHORISED":
                    self.process_xero_payment(payment)

            # Update last sync timestamp
            self.settings.last_payment_sync = frappe.utils.now()
            self.settings.save()
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(title="Xero Payment Sync", message=f"Xero Payment Sync Error: {str(e)}")

    def process_xero_payment(self, payment):
        if not payment.invoice:
            return

        # Get invoice number for matching
        if not payment.invoice.invoice_number:
            api = self.get_accounting_api()
            inv_res = api.get_invoice(self.settings.tenant_id, payment.invoice.invoice_id)
            if not inv_res.invoices:
                return
            xero_inv = inv_res.invoices[0]
            invoice_number = xero_inv.invoice_number
        else:
            invoice_number = payment.invoice.invoice_number

        # Check if Invoice exists in Frappe
        if not frappe.db.exists("Sales Invoice", invoice_number):
            # Try matching by Xero Invoice ID
            if payment.invoice.invoice_id:
                invoice_number = frappe.db.get_value("Sales Invoice",
                    {"custom_xero_invoice_id": payment.invoice.invoice_id}, "name")
            if not invoice_number:
                return

        invoice_doc = frappe.get_doc("Sales Invoice", invoice_number)

        if invoice_doc.outstanding_amount <= 0:
            return

        # Dedupe: check if Payment Entry already exists for this Xero payment
        xero_ref = f"XERO-{str(payment.payment_id)[:8]}"
        existing_pe = frappe.db.exists("Payment Entry", {
            "reference_no": xero_ref,
            "docstatus": ["!=", 2]
        })
        if existing_pe:
            return

        self.create_payment_entry(invoice_doc, payment.amount, payment.date, xero_ref)

    def create_payment_entry(self, invoice, amount, date, reference_no=None):
        from frappe.utils import getdate

        if self.settings.default_payment_account:
            bank_account = self.settings.default_payment_account
        else:
            company_doc = frappe.get_doc("Company", invoice.company)
            bank_account = company_doc.default_bank_account

        if not bank_account:
            accs = frappe.get_all("Account", filters={"account_type": "Bank", "company": invoice.company}, limit=1)
            if accs:
                bank_account = accs[0].name

        if not bank_account:
            frappe.log_error(title="Xero Payment Sync",
                message=f"No Bank Account found for Company {invoice.company}. Cannot sync Xero Payment.")
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
        pe.reference_no = reference_no or f"XERO-{invoice.name}"
        pe.reference_date = getdate(date)

        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "allocated_amount": amount
        })

        pe.flags.ignore_permissions = True
        pe.save()
        pe.submit()
        frappe.db.commit()

        # Update Xero status on invoice
        frappe.db.set_value("Sales Invoice", invoice.name, "custom_xero_status", "PAID")

    # =====================
    # Customer Sync (Frappe → Xero)
    # =====================

    def sync_customer_to_xero(self, customer_doc):
        """Sync a Frappe Customer to Xero as a contact."""
        if customer_doc.get("custom_xero_contact_id"):
            return  # Already linked

        api = self.get_accounting_api()
        contact_data = {"Name": customer_doc.customer_name}

        email = customer_doc.get("email_id") or ""
        phone = customer_doc.get("mobile_no") or ""
        if email:
            contact_data["EmailAddress"] = email
        if phone:
            contact_data["Phones"] = [{"PhoneType": "MOBILE", "PhoneNumber": phone}]

        try:
            created = api.create_contacts(self.settings.tenant_id, contacts=contact_data)
            if created.contacts:
                contact_id = created.contacts[0].contact_id
                frappe.db.set_value("Customer", customer_doc.name, {
                    "custom_xero_contact_id": contact_id,
                    "custom_xero_sync_date": frappe.utils.now()
                })
                frappe.db.commit()
        except Exception as e:
            frappe.log_error(title="Xero Customer Sync",
                message=f"Error syncing customer {customer_doc.name} to Xero: {str(e)}")


# =====================
# Helper
# =====================

def get_xero_connector():
    return XeroConnector()


# =====================
# Event Handlers (called from hooks)
# =====================

def sync_quotation(doc, method=None):
    """Hook: Quotation on_submit → sync to Xero."""
    if doc.docstatus != 1:
        return
    try:
        connector = get_xero_connector()
        if not connector.settings.enable_xero:
            return
        connector.create_quote(doc)
    except Exception as e:
        frappe.log_error(title="Xero Quote Sync Error", message=frappe.get_traceback())
        frappe.msgprint(_("Failed to sync Quote to Xero: {}").format(str(e)), indicator='orange')

def sync_invoice(doc, method=None):
    """Hook: Sales Invoice on_submit → sync to Xero."""
    if doc.docstatus != 1:
        return
    try:
        connector = get_xero_connector()
        if not connector.settings.enable_xero:
            return
        connector.create_invoice(doc)
    except Exception as e:
        frappe.log_error(title="Xero Invoice Sync Error", message=frappe.get_traceback())
        frappe.msgprint(_("Failed to sync Invoice to Xero: {}").format(str(e)), indicator='orange')

def sync_customer_to_xero(doc, method=None):
    """Hook: Customer after_insert → sync to Xero."""
    if doc.get("custom_xero_contact_id"):
        return  # Already linked (imported FROM Xero)
    try:
        connector = get_xero_connector()
        if not connector.settings.enable_xero:
            return
        connector.sync_customer_to_xero(doc)
    except Exception as e:
        frappe.log_error(title="Xero Customer Sync Error", message=frappe.get_traceback())

def sync_xero_payments():
    """Scheduler wrapper: hourly payment sync from Xero."""
    try:
        connector = get_xero_connector()
        if connector.settings.enable_xero:
            connector.sync_xero_payments()
    except Exception as e:
        frappe.log_error(title="Xero Payment Sync", message=f"Scheduled Xero Payment Sync Error: {str(e)}")

def sync_xero_quotes():
    """Scheduler wrapper: hourly quote status sync from Xero."""
    try:
        connector = get_xero_connector()
        if connector.settings.enable_xero:
            connector.sync_xero_quotes()
    except Exception as e:
        frappe.log_error(title="Xero Quote Sync", message=f"Scheduled Xero Quote Sync Error: {str(e)}")

def sync_xero_contacts():
    """Scheduler wrapper: daily contact sync from Xero."""
    try:
        connector = get_xero_connector()
        if connector.settings.enable_xero:
            connector.sync_xero_contacts()
    except Exception as e:
        frappe.log_error(title="Xero Contact Sync", message=f"Scheduled Xero Contact Sync Error: {str(e)}")
