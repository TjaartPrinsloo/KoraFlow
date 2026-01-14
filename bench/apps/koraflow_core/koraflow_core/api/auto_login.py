"""
Auto-login API for newly signed up users
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
			"hypothesisId": "F"
		}
		with open(log_path, "a") as f:
			f.write(json.dumps(log_entry) + "\n")
	except Exception as e:
		# Silently fail if logging doesn't work
		pass


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def auto_login_with_token(token, redirect_to=None):
	"""
	Auto-login a user using a signup token
	This can be called via AJAX (returns JSON) or via redirect (performs login and redirects)
	"""
	try:
		_log_debug("auto_login.py:auto_login_with_token", "Function called", {
			"token": token[:10] + "..." if token else None,
			"redirect_to": redirect_to,
			"method": frappe.request.method if frappe.request else None,
			"has_x_requested_with": frappe.request.headers.get("X-Requested-With") if frappe.request else None
		})
		
		# Get login credentials from cache
		login_data = frappe.cache.get_value(f"signup_auto_login:{token}")
		
		_log_debug("auto_login.py:auto_login_with_token", "Cache lookup result", {
			"has_login_data": bool(login_data),
			"user": login_data.get("user") if login_data else None
		})
		
		if not login_data:
			_log_debug("auto_login.py:auto_login_with_token", "No login data found", {})
			# If called via redirect, show error page
			if frappe.request and frappe.request.method == "GET" and not frappe.request.headers.get("X-Requested-With"):
				frappe.respond_as_web_page(
					_("Invalid Token"),
					_("The login token is invalid or has expired. Please try signing up again."),
					http_status_code=400
				)
			return {
				"success": False,
				"message": _("Invalid or expired login token")
			}
		
		import time
		if time.time() > login_data.get("expires", 0):
			_log_debug("auto_login.py:auto_login_with_token", "Token expired", {
				"expires": login_data.get("expires"),
				"current_time": time.time()
			})
			frappe.cache.delete_value(f"signup_auto_login:{token}")
			# If called via redirect, show error page
			if frappe.request and frappe.request.method == "GET" and not frappe.request.headers.get("X-Requested-With"):
				frappe.respond_as_web_page(
					_("Token Expired"),
					_("The login token has expired. Please try signing up again."),
					http_status_code=400
				)
			return {
				"success": False,
				"message": _("Login token has expired")
			}
		
		# If this is a GET request without X-Requested-With header, it's a redirect-based login
		# Perform full login and redirect (this sets cookies properly)
		# Also check if it's not an AJAX request (no Accept: application/json header)
		is_ajax = frappe.request and frappe.request.headers.get("Accept", "").startswith("application/json")
		is_redirect_request = frappe.request and frappe.request.method == "GET" and not frappe.request.headers.get("X-Requested-With") and not is_ajax
		_log_debug("auto_login.py:auto_login_with_token", "Request type check", {
			"is_redirect_request": is_redirect_request,
			"method": frappe.request.method if frappe.request else None,
			"has_x_requested_with": frappe.request.headers.get("X-Requested-With") if frappe.request else None
		})
		
		if is_redirect_request:
			_log_debug("auto_login.py:auto_login_with_token", "Processing redirect-based login", {
				"user": login_data["user"]
			})
			
			# Set form dict for login - must use frappe._dict() not plain dict
			frappe.local.form_dict = frappe._dict({
				"cmd": "login",
				"usr": login_data["user"],
				"pwd": login_data["password"]
			})
			
			# Perform login
			login_manager = LoginManager()
			
			_log_debug("auto_login.py:auto_login_with_token", "LoginManager result", {
				"login_manager_user": login_manager.user,
				"expected_user": login_data["user"],
				"login_successful": login_manager.user == login_data["user"],
				"session_user": frappe.session.user if hasattr(frappe, 'session') else None
			})
			
			if login_manager.user == login_data["user"]:
				# Login successful, delete token
				frappe.cache.delete_value(f"signup_auto_login:{token}")
				
				# Ensure session is committed
				frappe.db.commit()
				
				# CRITICAL: Ensure cookies are set before redirect
				# LoginManager.set_user_info() should have been called, but ensure cookies are initialized
				if hasattr(frappe.local, 'cookie_manager'):
					frappe.local.cookie_manager.init_cookies()
				
				# Redirect to intake form or specified redirect
				redirect_url = redirect_to or frappe.utils.sanitise_redirect(frappe.request.args.get("redirect_to")) or "/glp1-intake/new"
				_log_debug("auto_login.py:auto_login_with_token", "Redirecting after successful login", {
					"redirect_url": redirect_url,
					"session_user": frappe.session.user,
					"session_sid": frappe.session.sid if hasattr(frappe.session, 'sid') else None,
					"has_cookie_manager": hasattr(frappe.local, 'cookie_manager')
				})
				
				# For website routes (like web forms), always redirect directly
				# Don't use redirect_post_login for System Users as it redirects to /app/
				# Set response type and location directly for API redirects
				# The cookies will be included in the redirect response
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = redirect_url
				return
			else:
				_log_debug("auto_login.py:auto_login_with_token", "Login failed", {
					"login_manager_user": login_manager.user,
					"expected_user": login_data["user"]
				})
				frappe.respond_as_web_page(
					_("Login Failed"),
					_("Unable to log in. Please try signing up again."),
					http_status_code=401
				)
				return
		
		# AJAX call - try to login but cookies may not be set properly
		_log_debug("auto_login.py:auto_login_with_token", "Processing AJAX call", {
			"user": login_data["user"]
		})
		
		# Set form dict for login - must use frappe._dict() not plain dict
		frappe.local.form_dict = frappe._dict({
			"cmd": "login",
			"usr": login_data["user"],
			"pwd": login_data["password"]
		})
		
		# Perform login
		login_manager = LoginManager()
		
		_log_debug("auto_login.py:auto_login_with_token", "LoginManager result (AJAX)", {
			"login_manager_user": login_manager.user,
			"expected_user": login_data["user"],
			"login_successful": login_manager.user == login_data["user"],
			"session_user": frappe.session.user if hasattr(frappe, 'session') else None
		})
		
		if login_manager.user == login_data["user"]:
			# Login successful, delete token
			frappe.cache.delete_value(f"signup_auto_login:{token}")
			frappe.db.commit()
			
			_log_debug("auto_login.py:auto_login_with_token", "AJAX login successful", {
				"user": login_manager.user,
				"redirect_url": redirect_to or "/glp1-intake/new"
			})
			
			return {
				"success": True,
				"message": _("Login successful"),
				"user": login_manager.user,
				"redirect_url": redirect_to or "/glp1-intake/new"
			}
		else:
			_log_debug("auto_login.py:auto_login_with_token", "AJAX login failed", {
				"login_manager_user": login_manager.user,
				"expected_user": login_data["user"]
			})
			return {
				"success": False,
				"message": _("Login failed")
			}
			
	except Exception as e:
		_log_debug("auto_login.py:auto_login_with_token", "Exception occurred", {
			"error": str(e),
			"error_type": type(e).__name__
		})
		frappe.log_error(f"Error in auto_login_with_token: {str(e)}")
		# If called via redirect, show error page
		if frappe.request and frappe.request.method == "GET" and not frappe.request.headers.get("X-Requested-With"):
			frappe.respond_as_web_page(
				_("Error"),
				_("An error occurred during auto-login. Please try signing up again."),
				http_status_code=500
			)
		return {
			"success": False,
			"message": _("An error occurred during auto-login")
		}

