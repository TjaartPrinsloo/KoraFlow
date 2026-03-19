# Copyright (c) 2026, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Sales Agent Commission Detail Report
Line-item detail of all commission accruals for finance drill-down.
"""

import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, today


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "sales_agent", "label": _("Sales Agent"), "fieldtype": "Link", "options": "Sales Agent", "width": 160},
		{"fieldname": "patient", "label": _("Patient"), "fieldtype": "Link", "options": "Patient", "width": 150},
		{"fieldname": "invoice_reference", "label": _("Invoice"), "fieldtype": "Link", "options": "Sales Invoice", "width": 140},
		{"fieldname": "item_code", "label": _("Item"), "fieldtype": "Link", "options": "Item", "width": 150},
		{"fieldname": "accrued_amount", "label": _("Amount"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100},
		{"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 110},
	]


def get_data(filters):
	conditions = []
	values = {}

	from_date = filters.get("from_date") or get_first_day(today())
	to_date = filters.get("to_date") or today()
	values["from_date"] = getdate(from_date)
	values["to_date"] = getdate(to_date)
	conditions.append("DATE(sa.creation) BETWEEN %(from_date)s AND %(to_date)s")

	if filters.get("sales_agent"):
		conditions.append("sa.sales_agent = %(sales_agent)s")
		values["sales_agent"] = filters["sales_agent"]

	status_filter = filters.get("status")
	if status_filter and status_filter != "All":
		conditions.append("sa.status = %(status)s")
		values["status"] = status_filter

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(f"""
		SELECT
			sa.sales_agent,
			sa.patient,
			sa.invoice_reference,
			sa.item_code,
			sa.accrued_amount,
			sa.status,
			DATE(sa.creation) as date
		FROM `tabSales Agent Accrual` sa
		WHERE {where_clause}
		ORDER BY sa.creation DESC
	""", values, as_dict=True)

	return data
