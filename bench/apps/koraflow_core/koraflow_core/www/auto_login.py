"""
Auto-login page handler for newly signed up users
This is a page route (not API) so redirects work properly
"""

import frappe
from frappe import _
from frappe.auth import LoginManager
import json
import os


def _log_debug(location, message, data):
	"""Log debug information to file"""
	try:
		log_path = "/Users/tjaartprinsloo/Documents/KoraFlow/.cursor/debug.log"
		log_entry = {
			"location": location,
			"message": message,
			"data": data,
			"timestamp": frappe.utils.now(),
			"sessionId": "debug-session",
			"runId": "run1",
			"hypothesisId": "G"
		}
		with open(log_path, "a") as f:
			f.write(json.dumps(log_entry) + "\n")
	except Exception as e:
		# Silently fail if logging doesn't work
		pass


def get_context(context):
	"""Handle auto-login via page route (not API) so redirects work properly"""
	context.no_cache = 1
	
	# Get token from URL
	token = frappe.local.request.args.get("token")
	redirect_to = frappe.local.request.args.get("redirect_to") or "/glp1-intake"
	
	_log_debug("auto_login.py:get_context", "Page route called", {
		"token": token[:10] + "..." if token else None,
		"redirect_to": redirect_to,
		"current_user": frappe.session.user
	})
	
	if not token:
		_log_debug("auto_login.py:get_context", "No token provided", {})
		frappe.respond_as_web_page(
			_("Invalid Request"),
			_("No login token provided. Please try signing up again."),
			http_status_code=400
		)
		return
	
	# Get login credentials from cache
	login_data = frappe.cache.get_value(f"signup_auto_login:{token}")
	
	_log_debug("auto_login.py:get_context", "Cache lookup result", {
		"has_login_data": bool(login_data),
		"user": login_data.get("user") if login_data else None
	})
	
	if not login_data:
		_log_debug("auto_login.py:get_context", "No login data found", {})
		frappe.respond_as_web_page(
			_("Invalid Token"),
			_("The login token is invalid or has expired. Please try signing up again."),
			http_status_code=400
		)
		return
	
	import time
	if time.time() > login_data.get("expires", 0):
		_log_debug("auto_login.py:get_context", "Token expired", {
			"expires": login_data.get("expires"),
			"current_time": time.time()
		})
		frappe.cache.delete_value(f"signup_auto_login:{token}")
		frappe.respond_as_web_page(
			_("Token Expired"),
			_("The login token has expired. Please try signing up again."),
			http_status_code=400
		)
		return
	
	# Set form dict for login - must use frappe._dict() not plain dict
	# Include signup_token so custom authenticate can allow disabled Patient users
	frappe.local.form_dict = frappe._dict({
		"cmd": "login",
		"usr": login_data["user"],
		"pwd": login_data["password"],
		"signup_token": token  # Pass token for disabled user login
	})
	
	# Perform login
	login_manager = LoginManager()
	
	_log_debug("auto_login.py:get_context", "LoginManager result", {
		"login_manager_user": login_manager.user,
		"expected_user": login_data["user"],
		"login_successful": login_manager.user == login_data["user"],
		"session_user": frappe.session.user if hasattr(frappe, 'session') else None
	})
	
	if login_manager.user == login_data["user"]:
		# Login successful, delete token
		frappe.cache.delete_value(f"signup_auto_login:{token}")
		frappe.db.commit()
		
		# Sanitize redirect URL
		redirect_url = frappe.utils.sanitise_redirect(redirect_to) or "/glp1-intake"
		
		_log_debug("auto_login.py:get_context", "Redirecting after successful login", {
			"redirect_url": redirect_url,
			"session_user": frappe.session.user,
			"session_sid": frappe.session.sid if hasattr(frappe.session, 'sid') else None,
			"has_cookie_manager": hasattr(frappe.local, 'cookie_manager'),
			"cookies_count": len(frappe.local.cookie_manager.cookies) if hasattr(frappe.local, 'cookie_manager') else 0
		})
		
		# Return HTML page with meta refresh redirect
		# This ensures cookies are set in the response headers before redirect
		# LoginManager should have already set cookies via set_user_info()
		# Frappe's process_response will flush them to this HTML response
		# Then the meta refresh will redirect after cookies are set
		html = f"""<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<meta http-equiv="refresh" content="0;url={redirect_url}">
	<title>Logging you in...</title>
	<script>
		// Also use JavaScript redirect as backup
		setTimeout(function() {{
			window.location.href = {frappe.utils.json.dumps(redirect_url)};
		}}, 100);
	</script>
</head>
<body>
	<p>Logging you in... <a href="{redirect_url}">Click here if you are not redirected</a></p>
</body>
</html>"""
		
		# Return HTML response - cookies will be flushed by process_response
		frappe.response["type"] = "page"
		frappe.response["page_name"] = "auto_login_redirect"
		frappe.local.response.filecontent = html
		return
	else:
		_log_debug("auto_login.py:get_context", "Login failed", {
			"login_manager_user": login_manager.user,
			"expected_user": login_data["user"]
		})
		frappe.respond_as_web_page(
			_("Login Failed"),
			_("Unable to log in. Please try signing up again."),
			http_status_code=401
		)

