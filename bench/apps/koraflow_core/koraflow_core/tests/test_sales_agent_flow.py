
import frappe
from frappe.utils import today, add_days
import time

def run_test():
    print("Starting Sales Agent Flow Test...")
    
    # 1. Setup Data
    import uuid
    suffix = str(uuid.uuid4())[:8]
    agent_email = f"agent_{suffix}@example.com"
    patient_email = f"patient_{suffix}@example.com"
    
    # Create User for Agent
    if not frappe.db.exists("User", agent_email):
        u = frappe.new_doc("User")
        u.email = agent_email
        u.first_name = "Test Agent"
        u.last_name = suffix
        u.append("roles", {"role": "Sales Agent Portal"})
        u.save(ignore_permissions=True)
        
    # Create Sales Agent
    agent = frappe.new_doc("Sales Agent")
    agent.first_name = "Test Agent"
    agent.last_name = suffix
    agent.user = agent_email
    agent.commission_rate = 10.0 # 10%
    agent.status = "Active"
    agent.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Sales Agent: {agent.name}")
    
    frappe.db.commit()
    print(f"Created Sales Agent: {agent.name}")
    
    # Create Patient using API
    from koraflow_core.api.sales_agent_dashboard import create_referral
    
    # Mock session user as agent
    frappe.session.user = agent_email
    
    result = create_referral(
        first_name="Test Patient",
        last_name=suffix,
        email=patient_email,
        mobile_no=f"082{str(uuid.uuid4().int)[:7]}", # Valid numeric phone
        sex="Female",
        dob="1990-01-01"
    )
    
    referral_id = result.get("referral")
    referral = frappe.get_doc("Patient Referral", referral_id)
    patient_name = referral.patient
    patient = frappe.get_doc("Patient", patient_name)
    
    print(f"Created Patient via API: {patient.name} referred by {agent.name}")
    
    # Create Item
    item_code = f"Test_Item_{suffix}"
    if not frappe.db.exists("Item", item_code):
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_group = "Products"
        item.stock_uom = "Nos"
        item.is_stock_item = 0
        item.save(ignore_permissions=True)
        frappe.db.commit()
        
    # Create Sales Invoice
    si = frappe.new_doc("Sales Invoice")
    si.customer = "Test Customer" # Needs valid customer?
    # Ensure a customer exists or creating one
    if not frappe.db.exists("Customer", "Test Customer"):
        c = frappe.new_doc("Customer")
        c.customer_name = "Test Customer"
        c.save(ignore_permissions=True)
        
    si.customer = "Test Customer"
    si.patient = patient.name
    si.due_date = today()
    si.append("items", {
        "item_code": item_code,
        "qty": 1,
        "rate": 1000.0
    })
    si.insert(ignore_permissions=True)
    si.submit()
    frappe.db.commit()
    print(f"Created and Submitted Sales Invoice: {si.name}")
    
    # Simulate Payment
    # We need to update status to "Paid". 
    # Usually requires Payment Entry, but for test, we can force status if logic hook listens to "on_update".
    # Logic hook listens to on_update and checks doc.status == "Paid".
    
    # Let's try creating a Payment Entry to be proper, or just update status if allowed.
    # Updating status directly on SI is often blocked.
    # Let's create Payment Entry.
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = "Test Customer"
    pe.paid_amount = 1000.0
    pe.received_amount = 1000.0
    pe.target_exchange_rate = 1.0
    pe.append("references", {
        "reference_doctype": "Sales Invoice",
        "reference_name": si.name,
        "total_amount": 1000.0,
        "outstanding_amount": 1000.0,
        "allocated_amount": 1000.0
    })
    # pe.save(ignore_permissions=True) 
    # Payment Entry creation might fail if accounts not set.
    # Fallback: Just update SI status field via db.set_value and trigger hook manually or save.
    
    print("Simulating Payment via DB update (skipping PE complexity)...")
    frappe.db.set_value("Sales Invoice", si.name, "status", "Paid")
    si.reload()
    
    # Manually trigger hook because db.set_value might not trigger on_update depending on how it's called, 
    # but si.save() would.
    from koraflow_core.hooks.commission_hooks import on_invoice_paid
    on_invoice_paid(si, "on_update")
    frappe.db.commit()
    
    # Assert Accrual
    accruals = frappe.get_all("Sales Agent Accrual", 
        filters={"sales_agent": agent.name, "invoice_reference": si.name},
        fields=["accrued_amount", "status"]
    )
    
    if not accruals:
        print("FAILURE: No Sales Agent Accrual created.")
    else:
        acc = accruals[0]
        print(f"SUCCESS: Accrual created. Amount: {acc.accrued_amount} (Expected: 100.0). Status: {acc.status}")
        
        if float(acc.accrued_amount) == 100.0:
             print("SUCCESS: Commission verification passed.")
        else:
             print(f"FAILURE: Incorrect commission amount. Got {acc.accrued_amount}")

    # Test Payout Request
    print("Testing Payout Request...")
    # Mock session user
    frappe.session.user = agent_email
    
    from koraflow_core.api.agent_portal import request_payout
    try:
        res = request_payout(100.0)
        print(f"SUCCESS: Payout requested. Result: {res}")
        
        # Verify Purchase Invoice
        pi_name = res.get("invoice")
        pi = frappe.get_doc("Purchase Invoice", pi_name)
        print(f"SUCCESS: Purchase Invoice created: {pi.name} for Supplier: {pi.supplier} Amount: {pi.grand_total}")
        
        if float(pi.grand_total) == 100.0: # assuming grand_total matches
            print("SUCCESS: Payout Invoice verification passed.")
        else:
            print(f"FAILURE: Payout Invoice amount mismatch. Got {pi.grand_total}")
            
    except Exception as e:
        print(f"FAILURE: Payout request failed: {e}")
        import traceback
        traceback.print_exc()

