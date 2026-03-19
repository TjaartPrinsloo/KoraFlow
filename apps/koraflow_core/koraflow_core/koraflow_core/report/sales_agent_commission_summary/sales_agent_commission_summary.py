# Copyright (c) 2026, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Sales Agent Commission Summary Report
Aggregated view of commissions by sales agent for finance payout tracking.
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
		{"fieldname": "sales_agent", "label": _("Sales Agent"), "fieldtype": "Link", "options": "Sales Agent", "width": 180},
		{"fieldname": "total_referrals", "label": _("Referrals"), "fieldtype": "Int", "width": 90},
		{"fieldname": "total_accrued", "label": _("Accrued"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_requested", "label": _("Requested"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_paid", "label": _("Paid"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "grand_total", "label": _("Grand Total"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "outstanding_balance", "label": _("Outstanding"), "fieldtype": "Currency", "width": 140},
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
			COUNT(DISTINCT sa.patient) as total_referrals,
			SUM(CASE WHEN sa.status = 'Accrued' THEN sa.accrued_amount ELSE 0 END) as total_accrued,
			SUM(CASE WHEN sa.status = 'Requested' THEN sa.accrued_amount ELSE 0 END) as total_requested,
			SUM(CASE WHEN sa.status = 'Paid' THEN sa.accrued_amount ELSE 0 END) as total_paid,
			SUM(sa.accrued_amount) as grand_total,
			SUM(CASE WHEN sa.status IN ('Accrued', 'Requested') THEN sa.accrued_amount ELSE 0 END) as outstanding_balance
		FROM `tabSales Agent Accrual` sa
		WHERE {where_clause}
		GROUP BY sa.sales_agent
		ORDER BY grand_total DESC
	""", values, as_dict=True)

	return data
