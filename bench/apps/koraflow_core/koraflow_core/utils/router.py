# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def resolve_sales_agent_route(route):
	"""
	Override route resolution for Sales Agents
	Redirect /app, /app/build, /app/home to /app/sales-agent-dash for Sales Agents
	
	This is called by Frappe's website router for client-side routes.
	"""
	return None

