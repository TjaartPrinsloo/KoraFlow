"""
Installation Script: Create Injection Items and Medications
============================================================

This script creates injection items and their associated medications
based on a reference item (AMINO-GOLD-0.8ML).

Usage:
    bench --site [site-name] execute installation_scripts.create_injection_items.run

Or run directly:
    bench --site [site-name] console
    >>> exec(open('installation_scripts/create_injection_items.py').read())
"""

import frappe

REFERENCE_ITEM_CODE = "AMINO-GOLD-0.8ML"

ITEMS_TO_CREATE = [
    {"item_name": "Eco Injection 0.8ml", "price": 1000},
    {"item_name": "Gold Injection 0.8ml", "price": 1800},
    {"item_name": "Aminowell Injection 0.8ml", "price": 2750},
    {"item_name": "Eco Boost Injection 0.8ml", "price": 2500},
    {"item_name": "Ruby Injection 0.8ml", "price": 2500},
    {"item_name": "Titanium Injection 0.8ml", "price": 2500},
    {"item_name": "Ruby Boost Injection 0.8ml", "price": 2500},
    {"item_name": "Wolverine Stack Injection 0.8ml", "price": 2500},
    {"item_name": "Glow Stack Injection 0.8ml", "price": 2500},
    {"item_name": "NAD+ Injection 0.8ml", "price": 2500},
]


def run():
    """Main function to create all items and medications"""
    if not frappe.db.exists("Item", REFERENCE_ITEM_CODE):
        frappe.throw(f"Reference item {REFERENCE_ITEM_CODE} not found. Please ensure it exists before running this script.")

    ref_item = frappe.get_doc("Item", REFERENCE_ITEM_CODE)

    # Find linked medication from reference item
    ref_medication = frappe.get_all(
        "Medication Linked Item",
        filters={"item": ref_item.name},
        pluck="parent"
    )

    if not ref_medication:
        frappe.throw(f"Reference item {REFERENCE_ITEM_CODE} is not linked to a Medication. Please link it first.")

    ref_medication = frappe.get_doc("Medication", ref_medication[0])
    frappe.msgprint(f"Using reference Medication: {ref_medication.name}")

    created_count = 0
    skipped_count = 0

    for entry in ITEMS_TO_CREATE:
        result = create_item_and_medication(entry, ref_item, ref_medication)
        if result == "created":
            created_count += 1
        elif result == "skipped":
            skipped_count += 1

    frappe.db.commit()
    frappe.msgprint(
        f"✅ Injection medications created successfully! "
        f"Created: {created_count}, Skipped: {skipped_count}"
    )


def create_item_and_medication(entry, ref_item, ref_medication):
    """Create a single item and its associated medication"""
    item_name = entry["item_name"]
    item_code = item_name  # Use item_name as item_code

    if frappe.db.exists("Item", item_code):
        frappe.logger().info(f"Item already exists: {item_code}")
        return "skipped"

    # -------------------------------
    # Create Item (clone from reference)
    # -------------------------------
    item = frappe.new_doc("Item")
    item.item_code = item_code
    item.item_name = item_name
    item.item_group = ref_item.item_group
    item.stock_uom = ref_item.stock_uom
    item.is_stock_item = 1
    item.has_batch_no = ref_item.has_batch_no
    item.has_expiry_date = ref_item.has_expiry_date
    item.is_sales_item = 1
    item.is_purchase_item = 1

    # Healthcare / controlled drug fields
    item.is_prescription_item = 1
    item.is_controlled = 1

    # Copy any custom healthcare flags
    for field in ref_item.meta.fields:
        if field.fieldname.startswith("healthcare_") or field.fieldname.startswith("is_"):
            if hasattr(ref_item, field.fieldname):
                setattr(item, field.fieldname, getattr(ref_item, field.fieldname))

    item.insert(ignore_permissions=True)
    frappe.logger().info(f"Created Item: {item_code}")

    # -------------------------------
    # Create / link Medication
    # -------------------------------
    medication_name = item_name.replace(" Injection 0.8ml", "")

    if not frappe.db.exists("Medication", medication_name):
        medication = frappe.new_doc("Medication")
        medication.generic_name = medication_name  # This is the autoname field
        medication.medication_class = ref_medication.medication_class
        medication.strength = ref_medication.strength
        medication.strength_uom = ref_medication.strength_uom
        medication.dosage_form = ref_medication.dosage_form
        medication.is_prescription = 1
        medication.is_controlled = 1
        medication.description = "0.8ml injectable medication"
        medication.insert(ignore_permissions=True)
        frappe.logger().info(f"Created Medication: {medication_name}")
    else:
        medication = frappe.get_doc("Medication", medication_name)
        frappe.logger().info(f"Medication already exists: {medication_name}")

    # Link Item to Medication
    # Check if already linked
    already_linked = any(li.item == item.name for li in medication.linked_items)
    if not already_linked:
        medication.append("linked_items", {
            "item": item.name,
            "item_code": item.name,
            "is_billable": 1
        })
        medication.save(ignore_permissions=True)
        frappe.logger().info(f"Linked Item to Medication")
    else:
        frappe.logger().info(f"Item already linked to Medication")

    # -------------------------------
    # Add Price
    # -------------------------------
    price_list = frappe.db.get_value("Price List", {"selling": 1}, "name")
    if not price_list:
        # Create Standard Selling if it doesn't exist
        price_list = frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": "Standard Selling",
            "selling": 1,
            "enabled": 1,
            "currency": "ZAR"
        })
        price_list.insert(ignore_permissions=True)
        price_list = price_list.name
        frappe.logger().info(f"Created Price List: {price_list}")
    
    existing_price = frappe.db.get_value("Item Price", {
        "item_code": item.name,
        "price_list": price_list
    }, "name")
    
    if not existing_price:
        price = frappe.new_doc("Item Price")
        price.item_code = item.name
        price.price_list = price_list
        price.price_list_rate = entry["price"]
        price.selling = 1
        price.currency = frappe.db.get_value("Price List", price_list, "currency") or "ZAR"
        price.uom = item.stock_uom
        price.insert(ignore_permissions=True)
        frappe.logger().info(f"Created Item Price: R{entry['price']} ({price.currency}, {price.uom})")
    else:
        # Update existing price and ensure all fields are set
        price_doc = frappe.get_doc("Item Price", existing_price)
        price_doc.price_list_rate = entry["price"]
        price_doc.selling = 1
        price_doc.currency = frappe.db.get_value("Price List", price_list, "currency") or "ZAR"
        price_doc.uom = item.stock_uom
        price_doc.save(ignore_permissions=True)
        frappe.logger().info(f"Updated Item Price: R{entry['price']} ({price_doc.currency}, {price_doc.uom})")

    return "created"


if __name__ == "__main__":
    run()

