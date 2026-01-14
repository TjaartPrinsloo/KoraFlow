# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Override Frappe's default sign_up function to use passwordless patient signup
This override is applied at module load time to ensure it persists
"""

import frappe
from frappe import _


def override_sign_up():
	"""Override the default Frappe sign_up function"""
	# #region agent log
	import json, os
	log_path = "/Users/tjaartprinsloo/Documents/KoraFlow/.cursor/debug.log"
	try:
		with open(log_path, "a") as f:
			f.write(json.dumps({"id":"log_override_1","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:override_sign_up","message":"Override function called","data":{"has_frappe":hasattr(__import__("frappe"),"session")},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
	except: pass
	# #endregion
	
	from frappe.core.doctype.user import user as user_module
	
	# Store original function if not already stored
	if not hasattr(user_module, 'original_sign_up'):
		user_module.original_sign_up = user_module.sign_up
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_override_2","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:override_sign_up","message":"Original sign_up stored","data":{"original_exists":True},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
	
	# Create wrapper function that preserves the decorator
	def sign_up_wrapper(email: str, full_name: str, redirect_to: str = None) -> tuple[int, str]:
		"""
		Override default signup to use passwordless patient signup
		Password will be emailed after email verification
		"""
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_wrapper_1","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:sign_up_wrapper","message":"Wrapper called","data":{"email":email[:10]+"..." if email else None,"full_name":full_name[:20] if full_name else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
		
		from koraflow_core.api.patient_signup import patient_sign_up
		
		# Set redirect to wizard if not specified
		if not redirect_to:
			redirect_to = "/glp1-intake-wizard"
		
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_wrapper_2","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:sign_up_wrapper","message":"Calling patient_sign_up","data":{"redirect_to":redirect_to},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
		
		# Call passwordless patient signup
		result = patient_sign_up(email, full_name, redirect_to)
		
		# #region agent log
		try:
			with open(log_path, "a") as f:
				f.write(json.dumps({"id":"log_wrapper_3","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:sign_up_wrapper","message":"patient_sign_up returned","data":{"status":result[0] if isinstance(result,tuple) and len(result)>0 else None,"has_token":len(result)>3 if isinstance(result,tuple) else False},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
		except: pass
		# #endregion
		
		return result
	
	# Preserve the whitelist decorator from original function
	sign_up_wrapper = frappe.whitelist(allow_guest=True)(sign_up_wrapper)
	
	# Replace the function
	user_module.sign_up = sign_up_wrapper
	
	# #region agent log
	try:
		with open(log_path, "a") as f:
			f.write(json.dumps({"id":"log_override_3","timestamp":int(__import__("time").time()*1000),"location":"user_override.py:override_sign_up","message":"Override applied","data":{"sign_up_replaced":user_module.sign_up==sign_up_wrapper},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"})+"\n")
	except: pass
	# #endregion
	
	return sign_up_wrapper


# Apply override immediately when module is imported
try:
	override_sign_up()
except Exception as e:
	# If override fails (e.g., during initial setup), log but don't fail
	frappe.log_error(f"Could not override sign_up function: {str(e)}", "Signup Override Error")
