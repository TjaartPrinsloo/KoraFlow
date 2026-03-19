# Copyright (c) 2024, KoraFlow and Contributors
# License: MIT. See LICENSE

import json
import frappe
from frappe import _


@frappe.whitelist()
def get_workspace_sidebar_items():
	"""
	Override get_workspace_sidebar_items to restrict Sales Agents
	Sales Agents should only see the Sales Agent Dashboard workspace
	"""
	from frappe.desk.desktop import get_workspace_sidebar_items as original_get_workspace_sidebar_items

	# Get original sidebar items
	sidebar_items = original_get_workspace_sidebar_items()

	roles = frappe.get_roles()

	is_manager = "Sales Agent Manager" in roles or "System Manager" in roles or "Administrator" in roles

	# If user is a Sales Agent (and not a manager), show NO workspaces
	# They should only use the partner portal at /sales_agent_dashboard
	if "Sales Agent" in roles and not is_manager:
		sidebar_items["pages"] = []

	# If user is a Nurse (and not a manager/admin), only show the Nurse View workspace
	elif "Nurse" in roles and not is_manager:
		filtered_pages = []
		for page in sidebar_items.get("pages", []):
			if page.get("name") == "Nurse View":
				filtered_pages.append(page)

		sidebar_items["pages"] = filtered_pages

	# If user is a Pharmacist (and not a manager/admin), only show Pharmacy workspace
	elif "Pharmacist" in roles and not is_manager:
		filtered_pages = []
		for page in sidebar_items.get("pages", []):
			if page.get("name") == "Pharmacy":
				filtered_pages.append(page)

		sidebar_items["pages"] = filtered_pages

	# For managers who are NOT System Manager/Administrator, hide internal-only workspaces
	if is_manager and "System Manager" not in roles and "Administrator" not in roles:
		hidden_workspaces = {"Xero", "Sales Agent Dashboard", "Sales Agent Workspace"}
		sidebar_items["pages"] = [
			p for p in sidebar_items.get("pages", [])
			if p.get("name") not in hidden_workspaces
		]

	return sidebar_items


@frappe.whitelist()
@frappe.read_only()
def get_desktop_page(page):
	"""
	Override frappe.desk.desktop.get_desktop_page to filter Healthcare
	workspace shortcuts and cards for non-admin users.
	"""
	from frappe.desk.desktop import get_desktop_page as original_get_desktop_page

	result = original_get_desktop_page(page)

	page_data = json.loads(page) if isinstance(page, str) else page
	page_name = page_data.get("name", "")

	roles = frappe.get_roles()
	if "System Manager" in roles or "Administrator" in roles:
		return result

	# Filter Healthcare workspace for non-admin users
	if page_name == "Healthcare":
		if result.get("shortcuts") and result["shortcuts"].get("items"):
			result["shortcuts"]["items"] = [
				s for s in result["shortcuts"]["items"]
				if s.get("label") not in HEALTHCARE_HIDDEN_SHORTCUTS
				and s.get("link_to") not in HEALTHCARE_HIDDEN_SHORTCUTS
			]
		if result.get("cards") and result["cards"].get("items"):
			result["cards"]["items"] = [
				c for c in result["cards"]["items"]
				if c.get("label") not in HEALTHCARE_HIDDEN_CARDS
			]

	# Filter Accounting workspace
	if page_name == "Accounting":
		if result.get("shortcuts") and result["shortcuts"].get("items"):
			result["shortcuts"]["items"] = [
				s for s in result["shortcuts"]["items"]
				if s.get("label") not in ACCOUNTING_HIDDEN_SHORTCUTS
			]
		if result.get("cards") and result["cards"].get("items"):
			result["cards"]["items"] = [
				c for c in result["cards"]["items"]
				if c.get("label") not in ACCOUNTING_HIDDEN_CARDS
			]

	# Filter Stock workspace
	if page_name == "Stock":
		if result.get("shortcuts") and result["shortcuts"].get("items"):
			result["shortcuts"]["items"] = [
				s for s in result["shortcuts"]["items"]
				if s.get("label") not in STOCK_HIDDEN_SHORTCUTS
			]

	# Filter Selling workspace
	if page_name == "Selling":
		if result.get("shortcuts") and result["shortcuts"].get("items"):
			result["shortcuts"]["items"] = [
				s for s in result["shortcuts"]["items"]
				if s.get("label") not in SELLING_HIDDEN_SHORTCUTS
			]

	return result


# Healthcare cards/sections to hide for non-admin users
HEALTHCARE_HIDDEN_CARDS = {
	"Inpatient", "Rehabilitation and Physiotherapy", "Nursing",
	"Laboratory", "Service Units", "Terminology Mapping", "Reports",
}

HEALTHCARE_HIDDEN_LINKS = {
	"Medical Department", "Patient Care Type", "Clinical Procedure",
	"Service Request", "Inpatient Record",
	"Therapy Session", "Patient Assessment", "Therapy Plan",
	"Exercise Type", "Therapy Type", "Patient Assessment Template",
	"Nursing Task", "Lab Test",
	"Healthcare Service Unit",
	"Code Value", "Code System",
	"Patient Appointment Analytics", "Diagnosis Trends",
}

# Shortcuts to hide (by shortcut_name in content JSON)
HEALTHCARE_HIDDEN_SHORTCUTS = {
	"Healthcare Service Unit",
}

# Accounting cards/sections to hide for non-admin users
ACCOUNTING_HIDDEN_CARDS = {
	"Subscription Management", "Share Management",
}

ACCOUNTING_HIDDEN_LINKS = {
	"Accounts Settings",
}

ACCOUNTING_HIDDEN_SHORTCUTS = {
	"Learn Accounting", "Dashboard",
}

# Shortcuts to hide from Stock workspace for non-admin users
STOCK_HIDDEN_SHORTCUTS = {
	"Learn Inventory Management", "Dashboard",
}

# Shortcuts to hide from Selling workspace for non-admin users
SELLING_HIDDEN_SHORTCUTS = {
	"Learn Sales Management", "Dashboard",
}


def filter_healthcare_workspace(doc, method=None):
	"""
	Doc event hook on Workspace onload to filter workspace links,
	shortcuts, and content blocks for non System Manager / Administrator users.
	Handles Healthcare and Accounting workspaces.
	"""
	roles = frappe.get_roles()
	if "System Manager" in roles or "Administrator" in roles:
		return

	if doc.name == "Healthcare":
		_filter_workspace_sections(doc, HEALTHCARE_HIDDEN_CARDS, HEALTHCARE_HIDDEN_LINKS, HEALTHCARE_HIDDEN_SHORTCUTS)
	elif doc.name == "Accounting":
		_filter_workspace_sections(doc, ACCOUNTING_HIDDEN_CARDS, ACCOUNTING_HIDDEN_LINKS, ACCOUNTING_HIDDEN_SHORTCUTS)
	elif doc.name == "Stock":
		_filter_workspace_sections(doc, set(), set(), STOCK_HIDDEN_SHORTCUTS)
	elif doc.name == "Selling":
		_filter_workspace_sections(doc, set(), set(), SELLING_HIDDEN_SHORTCUTS)


def _filter_workspace_sections(doc, hidden_cards, hidden_links, hidden_shortcuts):
	"""Generic workspace section filter."""
	# 1. Filter links child table
	current_section = None
	section_map = {}
	for link in doc.links:
		if link.type == "Card Break":
			current_section = link.label
		else:
			section_map[link.name] = current_section

	doc.links = [
		link for link in doc.links
		if not _should_hide_link(link, section_map, hidden_cards, hidden_links)
	]

	# 2. Filter shortcuts child table
	if hidden_shortcuts:
		doc.shortcuts = [
			s for s in doc.shortcuts
			if s.label not in hidden_shortcuts
			and s.link_to not in hidden_shortcuts
		]

	# 3. Filter content JSON (controls what the frontend actually renders)
	if doc.content:
		try:
			blocks = json.loads(doc.content)
			filtered_blocks = []
			for block in blocks:
				if _should_hide_content_block_generic(block, hidden_cards, hidden_shortcuts):
					continue
				filtered_blocks.append(block)
			doc.content = json.dumps(filtered_blocks)
		except (json.JSONDecodeError, TypeError):
			pass


def _should_hide_link(link, section_map, hidden_cards, hidden_links):
	if link.type == "Card Break" and link.label in hidden_cards:
		return True
	if link.type == "Link":
		if hidden_links and (link.label in hidden_links or link.link_to in hidden_links):
			return True
		if section_map.get(link.name) in hidden_cards:
			return True
	return False


def _should_hide_content_block_generic(block, hidden_cards, hidden_shortcuts):
	"""Check if a content JSON block should be hidden."""
	block_type = block.get("type", "")
	data = block.get("data", {})

	if block_type == "shortcut" and hidden_shortcuts:
		shortcut_name = data.get("shortcut_name", "")
		if shortcut_name in hidden_shortcuts:
			return True

	if block_type == "card" and hidden_cards:
		card_name = data.get("card_name", "")
		if card_name in hidden_cards:
			return True

	return False
