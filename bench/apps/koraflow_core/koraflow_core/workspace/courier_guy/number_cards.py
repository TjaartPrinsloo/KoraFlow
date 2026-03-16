"""
Number Cards for Courier Guy Workspace
"""
import frappe
from frappe import _


def get_total_waybills():
	"""Get total number of waybills"""
	return frappe.db.count("Courier Guy Waybill")


def get_in_transit_waybills():
	"""Get number of waybills in transit"""
	return frappe.db.count("Courier Guy Waybill", {"status": "In Transit"})


def get_delivered_waybills():
	"""Get number of delivered waybills"""
	return frappe.db.count("Courier Guy Waybill", {"status": "Delivered"})


def get_pending_waybills():
	"""Get number of pending waybills (Draft + Created)"""
	return frappe.db.count("Courier Guy Waybill", {"status": ["in", ["Draft", "Created"]]})


@frappe.whitelist()
def get_courier_guy_stats():
	"""Get statistics for Courier Guy dashboard"""
	return {
		"total_waybills": get_total_waybills(),
		"in_transit": get_in_transit_waybills(),
		"delivered": get_delivered_waybills(),
		"pending": get_pending_waybills()
	}

