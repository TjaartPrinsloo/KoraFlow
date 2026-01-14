
import frappe

def mask_email(email):
    """
    Mask email address for POPIA/PAIA compliant logging.
    Example: johndoe@example.com -> j***@example.com
    """
    if not email or "@" not in email:
        return "********"
    
    try:
        user_part, domain_part = email.split("@", 1)
        if len(user_part) <= 1:
            return f"*{domain_part}"
        
        # Keep first char, mask rest of user part
        masked_user = user_part[0] + "*" * 3
        return f"{masked_user}@{domain_part}"
    except Exception:
        return "********"
