import frappe

def check_fields():
    meta = frappe.get_meta("Quotation")
    custom_fields = [df.fieldname for df in meta.fields if df.fieldname.startswith('custom_')]
    print("Custom Fields on Quotation:", custom_fields)

if __name__ == "__main__":
    frappe.connect()
    check_fields()
