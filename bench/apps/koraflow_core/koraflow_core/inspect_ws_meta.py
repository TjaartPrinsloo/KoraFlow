import frappe

def inspect_workspace_meta():
    meta = frappe.get_meta("Workspace")
    print(f"Workspace DocType Table Fields:")
    for d in meta.fields:
        if d.fieldtype == "Table":
            print(f" - {d.label} (FieldName: {d.fieldname}, Options/Table: {d.options})")

    # Also list all records in tabWorkspace to see if Nurse View is really there
    workspaces = frappe.get_all("Workspace", fields=["name", "public", "is_hidden", "module"])
    print("\nAll Workspaces:")
    for ws in workspaces:
        print(f" - {ws.name} (Public: {ws.public}, Hidden: {ws.is_hidden}, Module: {ws.module})")

if __name__ == "__main__":
    inspect_workspace_meta()
