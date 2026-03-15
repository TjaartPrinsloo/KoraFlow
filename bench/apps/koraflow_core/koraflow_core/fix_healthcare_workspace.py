import frappe
import json

def fix_healthcare_workspace():
    workspace_name = "Healthcare"
    old_card = "Total Patients Admitted"
    new_card = "Patient Pending Clinical Review"
    
    workspace = frappe.get_doc("Workspace", workspace_name)
    
    # Update content JSON string
    if workspace.content:
        try:
            content_data = json.loads(workspace.content)
            updated = False
            for block in content_data:
                if block.get("type") == "number_card" and block.get("data", {}).get("number_card_name") == old_card:
                    block["data"]["number_card_name"] = new_card
                    updated = True
                # Also check for already renamed but maybe label is wrong in data?
                elif block.get("type") == "number_card" and block.get("data", {}).get("number_card_name") == new_card:
                    # Ensure it's there
                    pass
            
            if updated:
                workspace.content = json.dumps(content_data)
                print("Updated content JSON string.")
        except Exception as e:
            print(f"Error parsing content JSON: {e}")

    # Update child table entries (just to be sure, although I did it via SQL/rename_doc)
    for card in workspace.number_cards:
        if card.number_card_name == old_card:
            card.number_card_name = new_card
            card.label = new_card
            print(f"Updated child table entry from {old_card} to {new_card}")
        elif card.number_card_name == new_card:
            card.label = new_card
            print(f"Ensured child table label is {new_card}")

    workspace.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("Workspace saved and cache cleared.")

if __name__ == "__main__":
    fix_healthcare_workspace()
