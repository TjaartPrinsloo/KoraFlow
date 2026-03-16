import frappe

def fix_doctor_roles():
    frappe.flags.in_patch = True
    doctor_roles = ["Nurse", "Physician", "Desk User"]
    all_modules = [m.name for m in frappe.get_all("Module Def")]
    allowed_modules = ["Healthcare"]
    blocked_modules = [m for m in all_modules if m not in allowed_modules]

    for email in ["andre.terblanche@koraflow.com", "marinda.scharneck@koraflow.com"]:
        if not frappe.db.exists("User", email):
            print(f"{email}: does not exist, skipping")
            continue

        user = frappe.get_doc("User", email)

        # Reset roles
        user.set("roles", [])
        for role in doctor_roles:
            user.append("roles", {"role": role})

        # Block all modules except Healthcare
        user.set("block_modules", [{"module": m} for m in blocked_modules])

        user.flags.ignore_permissions = True
        user.flags.in_nurse_update = True
        user.save()
        print(f"{email}: roles={[r.role for r in user.roles]}, blocked={len(blocked_modules)} modules")

    frappe.flags.in_patch = False
    frappe.db.commit()
    print("Done")

if __name__ == "__main__":
    fix_doctor_roles()
