# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe import _


class ReferralMessage(Document):
	def before_insert(self):
		"""Set initial values"""
		if not self.from_user:
			self.from_user = frappe.session.user
		if not self.created_at:
			self.created_at = frappe.utils.now()
		if not self.status:
			self.status = "Unread"
	
	def on_update(self):
		"""Handle status changes"""
		if self.has_value_changed("status") and self.status == "Read" and not self.read_at:
			self.read_at = frappe.utils.now()


@frappe.whitelist()
def create_message(referral, subject, message, to_user=None):
	"""Create a message from agent to sales team"""
	referral_doc = frappe.get_doc("Patient Referral", referral)
	
	# Determine recipient
	if not to_user:
		# Default to assigned sales team member or first Sales Agent Manager
		to_user = referral_doc.assigned_sales_team_member
		if not to_user:
			# Find a Sales Agent Manager
			managers = frappe.get_all(
				"User",
				filters={"enabled": 1},
				or_filters=[
					["name", "in", frappe.get_all("Has Role", filters={"role": "Sales Agent Manager"}, pluck="parent")]
				],
				limit=1,
				pluck="name"
			)
			if managers:
				to_user = managers[0]
			else:
				frappe.throw(_("No Sales Agent Manager found to receive message"))
	
	# Create message
	msg = frappe.get_doc({
		"doctype": "Referral Message",
		"referral": referral,
		"from_user": frappe.session.user,
		"to_user": to_user,
		"subject": subject,
		"message": message,
		"status": "Unread"
	})
	
	msg.insert(ignore_permissions=True)
	frappe.db.commit()
	
	# Send notification
	frappe.publish_realtime(
		event="notification",
		message={
			"type": "alert",
			"title": _("New Message"),
			"message": _("You have a new message regarding referral {0}").format(referral_doc.referral_id)
		},
		user=to_user
	)
	
	return {"name": msg.name}


@frappe.whitelist()
def get_messages_for_referral(referral):
	"""Get all messages for a referral"""
	messages = frappe.get_all(
		"Referral Message",
		filters={"referral": referral},
		fields=["*"],
		order_by="created_at desc"
	)
	
	return messages

