import frappe

def debug_block_list():
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    print(f"Total Modules: {len(all_modules)}")
    
    expected = [{"module": m} for m in all_modules if m not in ["Healthcare"]]
    print(f"Expected Block List Length: {len(expected)}")
    
    # Check if Healthcare is in expected
    hc_in_expected = any(d['module'] == 'Healthcare' for d in expected)
    print(f"Is Healthcare in expected block list? {hc_in_expected}")
    
    # Check if HR is in expected
    hr_in_expected = any(d['module'] == 'HR' for d in expected)
    print(f"Is HR in expected block list? {hr_in_expected}")

if __name__ == "__main__":
    debug_block_list()
