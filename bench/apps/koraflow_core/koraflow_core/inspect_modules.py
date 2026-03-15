import frappe

def inspect_modules():
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    print(f"All Modules: {all_modules}")
    print(f"Does 'Healthcare' exist in all_modules? {'Healthcare' in all_modules}")
    
    # Check for similar names
    for m in all_modules:
        if m.lower() == 'healthcare':
            print(f"Found match: '{m}' (len: {len(m)})")

if __name__ == "__main__":
    inspect_modules()
