# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Override email sending for development to prevent SMTP errors
"""

import frappe
from frappe import _


def override_email_send(email_queue, sender, recipient, message):
	"""
	Override email sending for development.
	Instead of sending via SMTP, just log the email.
	This prevents SMTP connection errors during development.
	"""
	# In development, just log the email instead of sending
	# This allows signup to succeed even without SMTP configured
	frappe.logger().info(f"[Email Override] Would send email to {recipient}")
	frappe.logger().info(f"[Email Override] Subject: {email_queue.subject if hasattr(email_queue, 'subject') else 'N/A'}")
	
	# Mark as sent in the queue to prevent retries
	if hasattr(email_queue, 'recipients'):
		for recipient_obj in email_queue.recipients:
			if recipient_obj.recipient == recipient:
				recipient_obj.status = "Sent"
				recipient_obj.is_mail_sent = 1
	
	# Update queue status
	if hasattr(email_queue, 'status'):
		email_queue.status = "Sent"
	
	# Log to Email Queue for debugging
	frappe.logger().info(f"[Email Override] Email logged (not sent) - Recipient: {recipient}, Queue: {email_queue.name}")
