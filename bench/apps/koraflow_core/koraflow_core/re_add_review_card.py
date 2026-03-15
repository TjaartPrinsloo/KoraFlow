import frappe

def re_add_review_card():
    card_name = "Patient Pending Clinical Review"
    workspace_name = "Healthcare"
    
    if not frappe.db.exists("Number Card", card_name):
        print(f"Card {card_name} does not exist!")
        return
        
    ws = frappe.get_doc("Workspace", workspace_name)
    
    # Check if it exists in child table
    found = False
    for card in ws.number_cards:
        if card.number_card_name == card_name:
            found = True
            print(f"Card {card_name} found in child table.")
            break
            
    if not found:
        ws.append("number_cards", {
            "number_card_name": card_name,
            "label": card_name
        })
        print(f"Appended {card_name} to Workspace child table.")

    ws.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("Workspace re-saved and cache cleared.")

if __name__ == "__main__":
    re_add_review_card()
