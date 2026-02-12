from frappe.model.document import Document

class SalesAgentCommissionRule(Document):
	def validate(self):
		if not self.item and not self.item_group:
			frappe.throw("Please specify either Item or Item Group")
