import frappe
from frappe.model.document import Document
from frappe import _


class GLP1IntakeForm(Document):
	def validate(self):
		"""Calculate BMI and validate contraindications"""
		self.calculate_bmi()
		self.validate_contraindications()
	
	def calculate_bmi(self):
		"""Calculate BMI based on height and weight"""
		if not self.calculated_bmi:
			# Get weight in kg
			weight_kg = None
			if self.weight_unit == "Kilograms" and self.weight_kg:
				weight_kg = self.weight_kg
			elif self.weight_unit == "Pounds" and self.weight_pounds:
				# Convert pounds to kg (1 lb = 0.453592 kg)
				weight_kg = self.weight_pounds * 0.453592
			
			# Get height in meters
			height_m = None
			if self.height_unit == "Centimeters" and self.height_cm:
				height_m = self.height_cm / 100
			elif self.height_unit == "Feet/Inches":
				if self.height_feet and self.height_inches:
					# Convert feet and inches to meters
					total_inches = (self.height_feet * 12) + self.height_inches
					height_m = total_inches * 0.0254
			
			# Calculate BMI: weight (kg) / height (m)^2
			if weight_kg and height_m and height_m > 0:
				bmi = weight_kg / (height_m ** 2)
				self.calculated_bmi = round(bmi, 2)
	
	def validate_contraindications(self):
		"""Validate absolute contraindications"""
		if self.medullary_thyroid_carcinoma or self.men2_syndrome:
			frappe.throw(
				_("Medullary Thyroid Carcinoma (MTC) or Multiple Endocrine Neoplasia Type 2 (MEN 2) is an absolute contraindication for GLP-1 agonists."),
				title=_("Absolute Contraindication")
			)

