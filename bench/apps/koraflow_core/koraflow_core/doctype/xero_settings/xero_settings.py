# Copyright (c) 2024, KoraFlow Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url
from frappe import _

class XeroSettings(Document):
	pass

@frappe.whitelist()
def xero_callback(code=None, state=None, error=None):
    """
    Callback endpoint for Xero OAuth flow.
    """
    if error:
        frappe.log_error(f"Xero Auth Error: {error}")
        frappe.msgprint(_("Xero Authentication failed: {}").format(error))
        return _("Authentication Failed")

    if not code:
        return _("No authentication code received")

    from koraflow_core.utils.xero_connector import get_xero_connector
    connector = get_xero_connector()
    
    success, msg = connector.callback(state, code)
    if success:
        frappe.msgprint(_("Successfully connected to Xero!"))
        # Close window script
        return """
        <script>
            window.close();
        </script>
        """
    else:
        return _("Failed to complete connection: {}").format(msg)

@frappe.whitelist()
def authorize():
    from koraflow_core.utils.xero_connector import get_xero_connector
    connector = get_xero_connector()
    url = connector.get_authorization_url()
    return url

