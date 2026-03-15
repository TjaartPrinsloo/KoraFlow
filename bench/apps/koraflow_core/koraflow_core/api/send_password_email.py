import frappe
from frappe import _
from frappe.utils import random_string
from frappe.utils.password import update_password

def send_temporary_password_email(user_email):
    """
    Generates a new random password for the user and sends it via email.
    Using a simpler approach: Reset password to a random string and email it.
    """
    try:
        if not frappe.db.exists("User", user_email):
            frappe.log_error(title="Send Password Email", message=f"User {user_email} not found for password email")
            return

        # Generate random password
        new_password = random_string(10)
        
        # Update user's password
        update_password(user_email, new_password)
        
        # Send email
        subject = _("Your Account Password - KoraFlow")
        message = f"""
        <p>Hello,</p>
        <p>Thank you for completing your intake form.</p>
        <p>Your account has been created. You can log in with the following credentials:</p>
        <p><strong>Username:</strong> {user_email}</p>
        <p><strong>Temporary Password:</strong> {new_password}</p>
        <p>Please change your password after your first login.</p>
        <p><a href="{frappe.utils.get_url()}/login">Login Here</a></p>
        <p>Best regards,<br>The KoraFlow Team</p>
        """
        
        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=message,
            now=True
        )
        
        frappe.logger().info(f"Temporary password email sent to {user_email}")
        
    except Exception as e:
        frappe.log_error(title="Send Password Email Error", message=f"Error sending temporary password to {user_email}: {str(e)}")
