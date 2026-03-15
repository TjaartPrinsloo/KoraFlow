# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
Complete Healthcare Dispensing System Setup
Creates medicines, items, warehouses, sales partners, users, and commission structure
"""

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days


# ============================================================================
# 1. MEDICINES & ITEMS
# ============================================================================

MEDICINES_DATA = [
	{"name": "Eco", "price": 1000},
	{"name": "Gold", "price": 1800},
	{"name": "Aminowell", "price": 2750},
	{"name": "Eco Boost", "price": 2500},
	{"name": "RUBY", "price": 2500},
	{"name": "Titanium", "price": 2500},
	{"name": "Ruby Boost", "price": 2500},
]

COMMISSION_DATA = {
	"Aminowell": 300,
	"Gold": 200,
	"Eco": 50,
	"RUBY": 250,
	"Ruby Boost": 250,
	"Eco Boost": 250,
	"Titanium": 250,
}


def setup_medicines_and_items():
	"""Create Medicine records and linked Item records"""
	
	# Get or create UOM
	uom = "Vial"
	if not frappe.db.exists("UOM", uom):
		frappe.get_doc({
			"doctype": "UOM",
			"uom_name": uom
		}).insert(ignore_permissions=True)
	
	# Get or create Medication Class
	medication_class = "GLP-1 Agonist"
	if not frappe.db.exists("Medication Class", medication_class):
		frappe.get_doc({
			"doctype": "Medication Class",
			"medication_class": medication_class
		}).insert(ignore_permissions=True)
	
	# Get or create Strength UOM (mg for injectables)
	strength_uom = "mg"
	if not frappe.db.exists("UOM", strength_uom):
		frappe.get_doc({
			"doctype": "UOM",
			"uom_name": strength_uom
		}).insert(ignore_permissions=True)
	
	# Get or create Dosage Form
	dosage_form = "Injection"
	if not frappe.db.exists("Dosage Form", dosage_form):
		frappe.get_doc({
			"doctype": "Dosage Form",
			"dosage_form": dosage_form
		}).insert(ignore_permissions=True)
	
	# Get or create Item Group
	item_group = "Medicines"
	if not frappe.db.exists("Item Group", item_group):
		frappe.get_doc({
			"doctype": "Item Group",
			"item_group_name": item_group,
			"parent_item_group": "All Item Groups"
		}).insert(ignore_permissions=True)
	
	# Get or create Price List
	price_list = "Standard Selling"
	if not frappe.db.exists("Price List", price_list):
		frappe.get_doc({
			"doctype": "Price List",
			"price_list_name": price_list,
			"selling": 1,
			"enabled": 1,
			"currency": "ZAR"
		}).insert(ignore_permissions=True)
	
	created_items = []
	
	for med_data in MEDICINES_DATA:
		med_name = med_data["name"]
		price = med_data["price"]
		
		# Create Medicine
		if not frappe.db.exists("Medication", med_name):
			medication = frappe.get_doc({
				"doctype": "Medication",
				"generic_name": med_name,
				"medication_class": medication_class,
				"strength": 2.5,  # Default strength (can be customized per medication)
				"strength_uom": strength_uom,
				"is_prescription": 1,
				"is_controlled": 1,
				"schedule": "S4",
				"default_duration_days": 30,
				"repeat_allowed": 1,
				"dosage_form": dosage_form,
				"description": f"{med_name} - 0.8ml injectable medication (Schedule 4)"
			})
			medication.insert(ignore_permissions=True)
			frappe.msgprint(_("Created Medication: {0}").format(med_name))
		else:
			medication = frappe.get_doc("Medication", med_name)
			# Update fields
			if not medication.medication_class:
				medication.medication_class = medication_class
			if not medication.strength:
				medication.strength = 2.5
			if not medication.strength_uom:
				medication.strength_uom = strength_uom
			medication.is_prescription = 1
			medication.is_controlled = 1
			medication.schedule = "S4"
			medication.default_duration_days = 30
			medication.repeat_allowed = 1
			if not medication.dosage_form:
				medication.dosage_form = dosage_form
			medication.save(ignore_permissions=True)
		
		# Create Item
		item_code = med_name
		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_code,
				"item_name": med_name,
				"item_group": item_group,
				"stock_uom": uom,
				"is_stock_item": 1,
				"maintain_stock": 1,
				"has_batch_no": 1,
				"has_expiry_date": 1,
				"is_sales_item": 1,
				"is_purchase_item": 1,
				"valuation_method": "FIFO",
				"shelf_life_in_days": 30,
				"description": f"{med_name} - 0.8ml vial (Schedule 4)"
			})
			item.insert(ignore_permissions=True)
			frappe.msgprint(_("Created Item: {0}").format(item_code))
		else:
			item = frappe.get_doc("Item", item_code)
			# Update required fields
			item.is_stock_item = 1
			item.maintain_stock = 1
			item.has_batch_no = 1
			item.has_expiry_date = 1
			item.valuation_method = "FIFO"
			item.shelf_life_in_days = 30
			item.save(ignore_permissions=True)
		
		# Link Item to Medication
		medication.reload()
		item_linked = False
		for linked_item in medication.linked_items:
			if linked_item.item == item_code:
				item_linked = True
				break
		
		if not item_linked:
			medication.append("linked_items", {
				"item": item_code,
				"item_code": item_code,
				"is_billable": 1
			})
			medication.save(ignore_permissions=True)
			frappe.msgprint(_("Linked Item {0} to Medication {1}").format(item_code, med_name))
		
		# Create Item Price
		if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list}):
			frappe.get_doc({
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": price_list,
				"price_list_rate": price,
				"currency": "ZAR"
			}).insert(ignore_permissions=True)
		else:
			item_price = frappe.get_doc("Item Price", {"item_code": item_code, "price_list": price_list})
			item_price.price_list_rate = price
			item_price.save(ignore_permissions=True)
		
		created_items.append(item_code)
	
	frappe.db.commit()
	frappe.msgprint(_("Created {0} medicines and items").format(len(created_items)))
	return created_items


# ============================================================================
# 2. WAREHOUSES
# ============================================================================

def setup_warehouses():
	"""Create physical and virtual warehouses"""
	
	company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {"is_group": 0}, "name")
	
	if not company:
		frappe.throw(_("No company found. Please create a company first."))
	
	# Physical Warehouse: PHARM-CENTRAL-COLD
	pharm_warehouse_name = "PHARM-CENTRAL-COLD"
	
	# Check if exists with any company suffix (ERPNext adds company suffix to warehouse name)
	existing_pharm = frappe.db.get_value("Warehouse", {"warehouse_name": pharm_warehouse_name}, "name")
	if not existing_pharm:
		# Try to find by name pattern (with company suffix)
		existing_pharm_list = frappe.get_all("Warehouse", filters={"warehouse_name": ["like", f"{pharm_warehouse_name}%"]}, fields=["name"], limit=1)
		if existing_pharm_list:
			existing_pharm = existing_pharm_list[0].name
	
	if not existing_pharm:
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": pharm_warehouse_name,
			"company": company,
			"is_group": 0
		})
		warehouse.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_("Created Warehouse: {0}").format(pharm_warehouse_name))
		pharm_warehouse_actual_name = warehouse.name
	else:
		pharm_warehouse_actual_name = existing_pharm
		frappe.msgprint(_("Warehouse {0} already exists: {1}").format(pharm_warehouse_name, existing_pharm))
	
	# Create Pharmacy Warehouse record (if DocType exists)
	# Note: Skip if DocType doesn't exist or if link validation fails
	try:
		if frappe.db.exists("DocType", "Pharmacy Warehouse"):
			# Check if exists by warehouse_name (unique field)
			existing_pharm_warehouse = frappe.db.get_value(
				"Pharmacy Warehouse",
				{"warehouse_name": pharm_warehouse_name},
				"name"
			)
			if not existing_pharm_warehouse:
				# Reload warehouse to ensure it's available
				frappe.clear_cache(doctype="Warehouse")
				pharm_warehouse = frappe.get_doc({
					"doctype": "Pharmacy Warehouse",
					"warehouse_name": pharm_warehouse_name,
					"erpnext_warehouse": pharm_warehouse_actual_name,
					"warehouse_type": "Physical",
					"is_licensed": 1,
					"pharmacy_license_number": "PHARM-LICENSE-001",
					"cold_chain_enabled": 1,
					"is_active": 1
				})
				pharm_warehouse.insert(ignore_permissions=True)
				frappe.db.commit()
			else:
				frappe.msgprint(_("Pharmacy Warehouse {0} already exists").format(pharm_warehouse_name))
	except Exception as e:
		# Continue without Pharmacy Warehouse record - not critical
		pass
	
	# Virtual Warehouses
	virtual_warehouses = [
		"VIRTUAL-HUB-DEL-MAS",
		"VIRTUAL-HUB-PAARL",
		"VIRTUAL-HUB-WORCHESTER"
	]
	
	for vw_name in virtual_warehouses:
		existing_vw = frappe.db.get_value("Warehouse", {"warehouse_name": vw_name}, "name")
		if not existing_vw:
			warehouse = frappe.get_doc({
				"doctype": "Warehouse",
				"warehouse_name": vw_name,
				"company": company,
				"is_group": 0,
				"allow_negative_stock": 0
			})
			warehouse.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(_("Created Virtual Warehouse: {0}").format(vw_name))
			vw_actual_name = warehouse.name
		else:
			vw_actual_name = existing_vw
			frappe.msgprint(_("Virtual Warehouse {0} already exists: {1}").format(vw_name, existing_vw))
		
		# Create Pharmacy Warehouse record (if DocType exists)
		try:
			if frappe.db.exists("DocType", "Pharmacy Warehouse"):
				existing_vw_pharm = frappe.db.get_value(
					"Pharmacy Warehouse",
					{"warehouse_name": vw_name},
					"name"
				)
				if not existing_vw_pharm:
					frappe.clear_cache(doctype="Warehouse")
					pharm_warehouse = frappe.get_doc({
						"doctype": "Pharmacy Warehouse",
						"warehouse_name": vw_name,
						"erpnext_warehouse": vw_actual_name,
						"warehouse_type": "Virtual",
						"is_licensed": 0,
						"cold_chain_enabled": 0,
						"is_active": 1
					})
					pharm_warehouse.insert(ignore_permissions=True)
					frappe.db.commit()
		except Exception as e:
			# Continue without Pharmacy Warehouse record - not critical
			pass
	
	frappe.db.commit()
	frappe.msgprint(_("Warehouse structure created successfully"))


# ============================================================================
# 3. SALES PARTNERS & COMMISSION
# ============================================================================

SALES_PARTNERS = [
	"Teneil Bierman",
	"Sonette Viljoen",
	"Liani Rossouw",
	"Jorine Rich",
	"Theresa Visser",
	"Karin Ferreira",
	"Cherise Delport"
]

def setup_sales_partners():
	"""Create Sales Partner records"""
	
	# Get or create default territory
	territory = "South Africa"
	if not frappe.db.exists("Territory", territory):
		frappe.get_doc({
			"doctype": "Territory",
			"territory_name": territory,
			"is_group": 0
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	
	for partner_name in SALES_PARTNERS:
		if not frappe.db.exists("Sales Partner", partner_name):
			sales_partner = frappe.get_doc({
				"doctype": "Sales Partner",
				"partner_name": partner_name,
				"territory": territory,
				"commission_rate": 0,  # Using item-wise commission instead
				"enabled": 1
			})
			
			# Mark Sonette Viljoen as employee-linked (if field exists)
			# Note: Skip partner_type if it doesn't exist or Employee type doesn't exist
			if partner_name == "Sonette Viljoen" and hasattr(sales_partner, 'partner_type'):
				try:
					# Only set if Partner Type DocType exists and Employee type exists
					if frappe.db.exists("DocType", "Partner Type"):
						if frappe.db.exists("Partner Type", "Employee"):
							sales_partner.partner_type = "Employee"
				except:
					pass  # Skip if Partner Type doesn't exist
			
			sales_partner.insert(ignore_permissions=True)
			frappe.msgprint(_("Created Sales Partner: {0}").format(partner_name))
	
	frappe.db.commit()
	frappe.msgprint(_("Sales Partners created successfully"))


def setup_commission_structure():
	"""Create Sales Partner Commission Rule DocType and commission rules"""
	
	# Create DocType if it doesn't exist
	if not frappe.db.exists("DocType", "Sales Partner Commission Rule"):
		create_commission_rule_doctype()
	
	# Create commission rules for each item
	for item_name, commission_amount in COMMISSION_DATA.items():
		# Create rule for each sales partner
		for partner_name in SALES_PARTNERS:
			rule_name = f"{partner_name} - {item_name}"
			if not frappe.db.exists("Sales Partner Commission Rule", rule_name):
				rule = frappe.get_doc({
					"doctype": "Sales Partner Commission Rule",
					"sales_partner": partner_name,
					"item": item_name,
					"commission_amount": commission_amount,
					"enabled": 1
				})
				rule.insert(ignore_permissions=True)
	
	frappe.db.commit()
	frappe.msgprint(_("Commission structure created successfully"))


def create_commission_rule_doctype():
	"""Create Sales Partner Commission Rule DocType"""
	
	doctype_json = {
		"doctype": "DocType",
		"name": "Sales Partner Commission Rule",
		"module": "Selling",
		"custom": 1,
		"fields": [
			{
				"fieldname": "sales_partner",
				"fieldtype": "Link",
				"label": "Sales Partner",
				"options": "Sales Partner",
				"reqd": 1,
				"in_list_view": 1
			},
			{
				"fieldname": "item",
				"fieldtype": "Link",
				"label": "Item",
				"options": "Item",
				"reqd": 1,
				"in_list_view": 1
			},
			{
				"fieldname": "commission_amount",
				"fieldtype": "Currency",
				"label": "Commission Amount",
				"reqd": 1,
				"in_list_view": 1
			},
			{
				"fieldname": "enabled",
				"fieldtype": "Check",
				"label": "Enabled",
				"default": 1
			}
		],
		"permissions": [
			{
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1
			},
			{
				"role": "Accounts User",
				"read": 1,
				"write": 1,
				"create": 1
			}
		]
	}
	
	doctype = frappe.get_doc(doctype_json)
	doctype.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.msgprint(_("Created DocType: Sales Partner Commission Rule"))


# ============================================================================
# 4. USERS & ROLES
# ============================================================================

USERS_DATA = [
	{
		"email": "anita.graham@koraflow.com",
		"first_name": "Anita",
		"last_name": "Graham",
		"roles": ["System Manager", "Healthcare Admin"]
	},
	{
		"email": "sonette.viljoen@koraflow.com",
		"first_name": "Sonette",
		"last_name": "Viljoen",
		"roles": ["System Manager", "Healthcare Admin"]
	},
	{
		"email": "carmen.vanderberg@koraflow.com",
		"first_name": "Carmen",
		"last_name": "van der Berg",
		"roles": ["System Manager", "Healthcare Admin"]
	},
	{
		"email": "zell.lombard@koraflow.com",
		"first_name": "Zell",
		"last_name": "Lombard",
		"roles": ["Administrator", "Healthcare Admin"]
	},
	{
		"email": "andre.scharneck@koraflow.com",
		"first_name": "Andre",
		"last_name": "Scharneck",
		"roles": ["Administrator", "Healthcare Admin"]
	},
	{
		"email": "bianca.vanderhoven@koraflow.com",
		"first_name": "Bianca",
		"last_name": "van der Hoven",
		"roles": ["Administrator", "Healthcare Admin"]
	},
	{
		"email": "elize.rossouw@koraflow.com",
		"first_name": "Elize",
		"last_name": "Rossouw",
		"roles": ["Accounts User", "Sales User"]
	},
	{
		"email": "nurse.lee@koraflow.com",
		"first_name": "Nurse",
		"last_name": "Lee",
		"roles": ["Nurse", "Healthcare User"]
	},
	{
		"email": "andre.terblanche@koraflow.com",
		"first_name": "Andre",
		"last_name": "Terblanche",
		"roles": ["Doctor", "Healthcare Practitioner"]
	},
	{
		"email": "marinda.scharneck@koraflow.com",
		"first_name": "Marinda",
		"last_name": "Scharneck",
		"roles": ["Doctor", "Healthcare Practitioner"]
	},
	{
		"email": "tjaart.prinsloo@koraflow.com",
		"first_name": "Tjaart",
		"last_name": "Prinsloo",
		"roles": ["System Administrator", "Administrator"]
	}
]


def setup_users():
	"""Create users and assign roles"""
	
	# Ensure System User type exists
	if not frappe.db.exists("User Type", "System User"):
		try:
			user_type = frappe.get_doc({
				"doctype": "User Type",
				"name": "System User",
				"is_standard": 0
			})
			user_type.insert(ignore_permissions=True)
			frappe.db.commit()
		except:
			pass  # Continue if creation fails
	
	for user_data in USERS_DATA:
		email = user_data["email"]
		
		if not frappe.db.exists("User", email):
			# Get default user_type from existing user
			default_user_type = frappe.db.get_value("User", {"user_type": ["!=", ""]}, "user_type") or None
			
			user = frappe.get_doc({
				"doctype": "User",
				"email": email,
				"first_name": user_data["first_name"],
				"last_name": user_data["last_name"],
				"send_welcome_email": 0,
				"enabled": 1
			})
			
			# Set user_type if we found a default
			if default_user_type:
				user.user_type = default_user_type
			
			user.insert(ignore_permissions=True)
			frappe.msgprint(_("Created User: {0}").format(email))
		else:
			user = frappe.get_doc("User", email)
		# Ensure user_type is set (use existing user's type or default)
		if not user.user_type:
			# Get default from existing user or use first available
			default_user_type = frappe.db.get_value("User", {"user_type": ["!=", ""]}, "user_type") or None
			if default_user_type:
				user.user_type = default_user_type
			else:
				# Try to use System User, but skip if it doesn't exist
				try:
					if frappe.db.exists("User Type", "System User"):
						user.user_type = "System User"
				except:
					pass
		
		# Assign roles (only if role exists)
		roles_to_add = []
		for role in user_data["roles"]:
			if frappe.db.exists("Role", role):
				if not frappe.db.exists("Has Role", {"parent": email, "role": role}):
					roles_to_add.append(role)
			else:
				frappe.msgprint(_("Warning: Role '{0}' does not exist, skipping for user {1}").format(role, email))
		
		if roles_to_add:
			for role in roles_to_add:
				user.append("roles", {
					"role": role
				})
			user.save(ignore_permissions=True)
	
	frappe.db.commit()
	frappe.msgprint(_("Users created and roles assigned successfully"))


# ============================================================================
# MAIN SETUP FUNCTION
# ============================================================================

def setup_healthcare_dispensing_system():
	"""Complete setup of healthcare dispensing system"""
	
	frappe.msgprint(_("Starting healthcare dispensing system setup..."))
	
	# 1. Medicines and Items
	frappe.msgprint(_("Creating medicines and items..."))
	setup_medicines_and_items()
	
	# 2. Warehouses
	frappe.msgprint(_("Creating warehouses..."))
	setup_warehouses()
	
	# 3. Sales Partners
	frappe.msgprint(_("Creating sales partners..."))
	setup_sales_partners()
	
	# 4. Commission Structure
	frappe.msgprint(_("Creating commission structure..."))
	setup_commission_structure()
	
	# 5. Users and Roles
	frappe.msgprint(_("Creating users and assigning roles..."))
	setup_users()
	
	# 6. Custom Fields
	frappe.msgprint(_("Setting up custom fields..."))
	try:
		from koraflow_core.setup_custom_fields import setup_custom_fields
		setup_custom_fields()
	except Exception as e:
		frappe.log_error(title="Setup Error", message=f"Error setting up custom fields: {str(e)}")
	
	frappe.msgprint(_("Healthcare dispensing system setup completed successfully!"))


if __name__ == "__main__":
	setup_healthcare_dispensing_system()
