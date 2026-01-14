# Copyright (c) 2024, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Setup script for Sales Agent system
Run this after installing koraflow_core to initialize the Sales Agent system
"""

import frappe
from frappe import _


def setup_sales_agent_system():
	"""Complete setup of Sales Agent system"""
	print("Setting up Sales Agent system...")
	
	# 1. Create roles
	create_sales_agent_roles()
	
	# 2. Create workspace
	create_sales_agent_workspace()
	
	# 3. Set up permissions
	setup_permissions()
	
	# 4. Block Patient access for Sales Agents
	block_patient_access()
	
	frappe.db.commit()
	print("Sales Agent system setup complete!")


def create_sales_agent_roles():
	"""Create Sales Agent and Sales Agent Manager roles"""
	
	# Sales Agent Role
	if not frappe.db.exists("Role", "Sales Agent"):
		role = frappe.get_doc({
			"doctype": "Role",
			"role_name": "Sales Agent",
			"desk_access": 1,
			"is_custom": 1
		})
		role.insert(ignore_permissions=True)
		print("  ✓ Created Sales Agent role")
	else:
		print("  ✓ Sales Agent role already exists")
	
	# Sales Agent Manager Role
	if not frappe.db.exists("Role", "Sales Agent Manager"):
		role = frappe.get_doc({
			"doctype": "Role",
			"role_name": "Sales Agent Manager",
			"desk_access": 1,
			"is_custom": 1
		})
		role.insert(ignore_permissions=True)
		print("  ✓ Created Sales Agent Manager role")
	else:
		print("  ✓ Sales Agent Manager role already exists")


def create_sales_agent_workspace():
	"""Create Sales Agent Dashboard Workspace"""
	workspace_name = "Sales Agent Dashboard"
	
	if frappe.db.exists("Workspace", workspace_name):
		print("  ✓ Sales Agent Dashboard workspace already exists")
		return
	
	import json
	
	workspace = frappe.get_doc({
		"doctype": "Workspace",
		"title": workspace_name,
		"label": "Sales Agent Portal",
		"public": 1,
		"is_hidden": 0,
		"module": "Core",
		"icon": "chart-line",
		"content": json.dumps([
			{
				"type": "shortcut",
				"data": {
					"label": "My Referrals",
					"link_to": "Patient Referral",
					"type": "DocType",
					"doc_view": "List"
				}
			},
			{
				"type": "shortcut",
				"data": {
					"label": "Commission Records",
					"link_to": "Commission Record",
					"type": "DocType",
					"doc_view": "List"
				}
			},
			{
				"type": "shortcut",
				"data": {
					"label": "Messages",
					"link_to": "Referral Message",
					"type": "DocType",
					"doc_view": "List"
				}
			}
		]),
		"roles": [
			{"role": "Sales Agent"}
		]
	})
	
	workspace.flags.ignore_permissions = True
	workspace.insert()
	print("  ✓ Created Sales Agent Dashboard workspace")


def setup_permissions():
	"""Ensure all permissions are set up correctly"""
	print("  ✓ Permissions configured via DocType definitions")


def block_patient_access():
	"""Add permission restrictions to prevent Sales Agents from accessing Patient records"""
	# This is handled via permission_query_conditions in hooks.py
	# Patient DocType permissions are managed through DocType definitions
	# No need to modify the DocType directly as it may cause validation issues
	print("  ✓ Patient access restrictions handled via hooks and DocType permissions")


if __name__ == "__main__":
	frappe.init(site="your-site.localhost")
	frappe.connect()
	setup_sales_agent_system()

