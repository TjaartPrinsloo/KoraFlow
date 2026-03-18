"""
Prescription Generator Utility
Generates SAHPRA-compliant prescription PDFs from Patient Encounter and attaches to Patient Encounter record
(attached to encounter, not patient, to avoid cluttering the Patient attachments sidebar)
"""
import frappe
from frappe import _
from frappe.utils import formatdate, now
from frappe.utils.print_utils import get_print
from frappe.utils.file_manager import save_file


def get_practitioner_prescription_print_format(practitioner):
	"""
	Get the print format to use for prescription generation.
	Returns practitioner's preferred format or default SAHPRA format.
	
	Args:
		practitioner: Healthcare Practitioner name or doc
		
	Returns:
		str: Print Format name
	"""
	if isinstance(practitioner, str):
		practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	else:
		practitioner_doc = practitioner
	
	# Check if practitioner has a preferred print format
	if hasattr(practitioner_doc, 'prescription_print_format') and practitioner_doc.prescription_print_format:
		# Verify the print format exists
		if frappe.db.exists("Print Format", practitioner_doc.prescription_print_format):
			return practitioner_doc.prescription_print_format
	
	# Priority 1: Slim 2 Well Prescription
	custom_format = "Slim 2 Well Prescription"
	if frappe.db.exists("Print Format", custom_format):
		return custom_format
		
	# Priority 2: SAHPRA Prescription format
	default_format = "SAHPRA Prescription"
	if frappe.db.exists("Print Format", default_format):
		return default_format
	
	# Fallback to Encounter Print if others don't exist
	fallback_format = "Encounter Print"
	if frappe.db.exists("Print Format", fallback_format):
		return fallback_format
	
	# Last resort: Standard format
	return "Standard"


def generate_prescription_pdf(encounter, practitioner=None):
	"""
	Generate prescription PDF from Patient Encounter.
	Uses practitioner's PDF template if available, otherwise uses print format.
	
	Args:
		encounter: Patient Encounter name or doc
		practitioner: Healthcare Practitioner name or doc (optional, will be fetched from encounter if not provided)
		
	Returns:
		bytes: PDF content as bytes
	"""
	if isinstance(encounter, str):
		encounter_doc = frappe.get_doc("Patient Encounter", encounter)
	else:
		encounter_doc = encounter
	
	# Get practitioner from encounter if not provided
	if not practitioner:
		practitioner = encounter_doc.practitioner
	
	if not practitioner:
		frappe.throw(_("No practitioner found in encounter. Cannot generate prescription."))
	
	# Get practitioner doc
	if isinstance(practitioner, str):
		practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	else:
		practitioner_doc = practitioner
	
	# Method 1: If practitioner has a PDF template, use it as base and overlay data
	if hasattr(practitioner_doc, 'prescription_template') and practitioner_doc.prescription_template:
		try:
			pdf_content = generate_pdf_from_template(encounter_doc, practitioner_doc)
			if pdf_content and isinstance(pdf_content, bytes) and pdf_content.startswith(b'%PDF'):
				return pdf_content
			else:
				frappe.logger().warning("PDF template overlay did not return valid PDF, falling back to print format")
		except Exception as template_error:
			frappe.logger().warning(f"Failed to use PDF template, falling back to print format: {template_error}")
			# Continue to print format method
	
	# Method 2: Use print format (standard approach)
	print_format = get_practitioner_prescription_print_format(practitioner_doc)
	
	# Generate PDF - try multiple methods
	try:
		from frappe.utils.print_utils import get_print
		
		# Try weasyprint PrintFormatGenerator (best for custom Jinja templates)
		try:
			from frappe.utils.weasyprint import PrintFormatGenerator
			generator = PrintFormatGenerator(print_format, encounter_doc, letterhead=None)
			pdf_content = generator.render_pdf()
			return pdf_content
		except Exception as weasyprint_error:
			frappe.logger().info(f"WeasyPrint not available: {weasyprint_error}")
		
		# Try get_print with as_pdf=True (uses configured PDF generator)
		try:
			pdf_content = get_print(
				doctype="Patient Encounter",
				name=encounter_doc.name,
				print_format=print_format,
				as_pdf=True,
				no_letterhead=0
			)
			if pdf_content:
				return pdf_content
		except Exception as pdf_error:
			frappe.logger().info(f"PDF generation via get_print failed: {pdf_error}")
		
		# Fallback - save as HTML if PDF generation is not available
		frappe.logger().warning(
			"PDF generation not available. Saving prescription as HTML instead. "
			"Install wkhtmltopdf or weasyprint dependencies for PDF generation."
		)
		html_content = get_print(
			doctype="Patient Encounter",
			name=encounter_doc.name,
			print_format=print_format,
			as_pdf=False,
			no_letterhead=0
		)
		return html_content.encode('utf-8')
			
	except Exception as e:
		frappe.log_error(
			message=f"Error generating prescription PDF for encounter {encounter_doc.name}: {str(e)}",
			title="Prescription Generation Error"
		)
		raise


def generate_pdf_from_template(encounter_doc, practitioner_doc):
	"""
	Generate prescription PDF by overlaying data on practitioner's PDF template.
	Uses coordinate-based text overlay to fill the template.
	
	Args:
		encounter_doc: Patient Encounter document
		practitioner_doc: Healthcare Practitioner document
		
	Returns:
		bytes: Filled PDF content
	"""
	import io
	import os
	
	# Get the template PDF file
	template_file_url = practitioner_doc.prescription_template
	template_file = frappe.get_doc("File", {"file_url": template_file_url})
	template_path = template_file.get_full_path()
	
	if not os.path.exists(template_path):
		raise Exception(f"Template PDF not found at {template_path}")
	
	# Try to use pypdf and reportlab to overlay text on PDF
	try:
		from pypdf import PdfReader, PdfWriter
		from reportlab.pdfgen import canvas
		from reportlab.lib.pagesizes import A4
		from reportlab.lib.colors import black
		
		# Read the template PDF into memory
		with open(template_path, 'rb') as f:
			template_data = f.read()
		
		template_pdf = PdfReader(io.BytesIO(template_data))
		
		# Get page dimensions
		page = template_pdf.pages[0]
		mediabox = page.mediabox
		page_width = float(mediabox.width)
		page_height = float(mediabox.height)
		
		# Create overlay PDF with prescription data
		packet = io.BytesIO()
		can = canvas.Canvas(packet, pagesize=(page_width, page_height))
		can.setFillColor(black)
		
		# Collect all data to overlay
		data = get_prescription_data_for_overlay(encounter_doc, practitioner_doc)
		
		# Get coordinate mapping (can be customized per practitioner)
		# Default coordinates - these should be adjusted to match your PDF template layout
		coords = get_prescription_coordinates(practitioner_doc, page_width, page_height)
		
		# Set default font
		font_name = coords.get('font_name', 'Helvetica')
		font_size = coords.get('font_size', 10)
		can.setFont(font_name, font_size)
		
		# Helper function to draw text with custom font size if specified
		def draw_text(field_key, text_value, default_max_length=50):
			if not coords.get(field_key):
				return
			field_coords = coords[field_key]
			x = field_coords.get('x', 50)
			y = field_coords.get('y', page_height - 100)
			max_len = field_coords.get('max_length', default_max_length)
			font_sz = field_coords.get('font_size', font_size)
			
			if text_value:
				can.setFont(font_name, font_sz)
				can.drawString(x, y, str(text_value)[:max_len])
		
		# ONLY OVERLAY: Patient name, Date, and Medications
		# Practitioner details are already on the template - don't overlay them
		
		# 1. Patient Name in "Patient Name:" placeholder
		draw_text('patient_name_placeholder', data.get('patient_name', ''))
		
		# 2. Date in "Date:" placeholder
		date_str = frappe.utils.formatdate(data.get('encounter_date', frappe.utils.today()), 'dd MMM yyyy')
		draw_text('date_placeholder', date_str)
		
		# 3. Medications in empty space below - SAHPRA Narrative Format
		med_config = coords.get('medications', {})
		med_y_start = med_config.get('y_start', page_height - 480)
		med_line_height = med_config.get('line_height', 15)  # Smaller line height for multi-line format
		med_spacing = med_config.get('medication_spacing', 40)  # Space between medications
		med_y = med_y_start
		med_font_size = med_config.get('font_size', 9)
		
		if data.get('medications'):
			for idx, med in enumerate(data['medications']):
				if idx >= med_config.get('max_items', 10):
					break
				
				med_x = med_config.get('x', 50)
				current_y = med_y
				
				# Medicine name (bold/emphasized)
				can.setFont(font_name, med_config.get('name_font_size', 10))
				med_name = med.get('name', 'N/A')
				can.drawString(med_x, current_y, med_name)
				current_y -= med_line_height
				
				# Strength
				if med.get('strength'):
					can.setFont(font_name, med_font_size)
					strength_text = f"Strength: {med.get('strength')}"
					can.drawString(med_x, current_y, strength_text)
					current_y -= med_line_height
				
				# Dose
				if med.get('dosage'):
					can.setFont(font_name, med_font_size)
					dose_text = f"Dose: {med.get('dosage')}"
					can.drawString(med_x, current_y, dose_text)
					current_y -= med_line_height
				
				# Route
				if med.get('route'):
					can.setFont(font_name, med_font_size)
					route_text = f"Route: {med.get('route')}"
					can.drawString(med_x, current_y, route_text)
					current_y -= med_line_height
				
				# Frequency
				if med.get('frequency'):
					can.setFont(font_name, med_font_size)
					frequency_text = f"Frequency: {med.get('frequency')}"
					can.drawString(med_x, current_y, frequency_text)
					current_y -= med_line_height
				
				# Duration
				if med.get('duration'):
					can.setFont(font_name, med_font_size)
					duration_text = f"Duration: {med.get('duration')}"
					can.drawString(med_x, current_y, duration_text)
					current_y -= med_line_height
				
				# Quantity
				if med.get('quantity'):
					can.setFont(font_name, med_font_size)
					quantity_text = f"Quantity: {med.get('quantity')}"
					can.drawString(med_x, current_y, quantity_text)
					current_y -= med_line_height
				
				# Repeats
				if med.get('repeats'):
					can.setFont(font_name, med_font_size)
					repeats_text = f"Repeats: {med.get('repeats')}"
					can.drawString(med_x, current_y, repeats_text)
					current_y -= med_line_height
				
				# Move down for next medication
				med_y = current_y - med_spacing
		
		can.save()
		packet.seek(0)
		overlay_pdf = PdfReader(packet)
		
		# Merge overlay with template
		writer = PdfWriter()
		template_page = template_pdf.pages[0]
		overlay_page = overlay_pdf.pages[0]
		template_page.merge_page(overlay_page)
		writer.add_page(template_page)
		
		# Write to bytes
		output = io.BytesIO()
		writer.write(output)
		output.seek(0)
		
		return output.read()
		
	except ImportError as ie:
		# If pypdf/reportlab not available, fall back to print format
		raise Exception(f"PDF template filling requires pypdf and reportlab libraries. Install with: pip install pypdf reportlab. Error: {ie}")
	except Exception as e:
		frappe.log_error(title="Prescription PDF Fill Error", message=f"Error filling PDF template: {str(e)}")
		# Don't raise - fall back to print format instead
		frappe.logger().warning(f"PDF template overlay failed, will use print format: {e}")
		raise


def get_quantity_display(drug_name=None, strength=None, dosage=None, interval_days=7, duration_days=None, drug_code=None, medication=None):
	"""
	Calculate medication quantity and return formatted string with numerals and words.
	E.g., "1 (one) vial (0.8 ml)" or "4 (four) cartridges"

	Can be called from Jinja print formats via frappe.call().

	Args:
		drug_name: Name of the drug (for logging)
		strength: Strength string (unused, for context)
		dosage: Dosage string or Prescription Dosage name
		interval_days: Days between doses (default 7 for weekly)
		duration_days: Total duration in days
		drug_code: Item code for the drug
		medication: Medication doctype name

	Returns:
		str: Formatted quantity string, or empty string if calculation not possible
	"""
	import math
	import re

	if not duration_days:
		return ''

	# Parse dosage amount
	dosage_amount = None
	dosage_uom = 'ml'

	if dosage:
		try:
			dosage_doc = frappe.get_doc('Prescription Dosage', dosage)
			if hasattr(dosage_doc, 'dosage_strength') and dosage_doc.dosage_strength:
				for ds in dosage_doc.dosage_strength:
					if hasattr(ds, 'strength') and ds.strength:
						dosage_amount = float(ds.strength)
						if hasattr(ds, 'strength_uom') and ds.strength_uom:
							dosage_uom = str(ds.strength_uom)
						break
		except Exception:
			match = re.search(r'(\d+\.?\d*)\s*(ml|mg|g)', str(dosage), re.IGNORECASE)
			if match:
				dosage_amount = float(match.group(1))
				dosage_uom = match.group(2).lower()

	if not dosage_amount:
		return ''

	# Get item doc for vial volume
	item_doc = None
	if drug_code:
		try:
			item_doc = frappe.get_doc('Item', drug_code)
		except Exception:
			pass

	if not item_doc and medication:
		try:
			medication_doc = frappe.get_doc('Medication', medication)
			if hasattr(medication_doc, 'linked_items') and medication_doc.linked_items:
				linked_item_code = medication_doc.linked_items[0].item
				if linked_item_code:
					item_doc = frappe.get_doc('Item', linked_item_code)
		except Exception:
			pass

	if not item_doc:
		return ''

	vial_volume = getattr(item_doc, 'volume', None)
	vial_volume_uom = getattr(item_doc, 'volume_uom', 'ml') or 'ml'

	if not vial_volume:
		return ''

	try:
		# Calculate doses
		if interval_days == 7:
			doses = int(duration_days / 7)
		else:
			doses = int(duration_days / interval_days) if interval_days > 0 else 1

		if doses < 1:
			doses = 1

		total_volume = dosage_amount * doses
		vials_needed = math.ceil(total_volume / vial_volume)

		# Format with numerals and words
		try:
			vials_word = frappe.utils.in_words(vials_needed).strip()
		except Exception:
			vials_word = str(vials_needed)

		unit = "vial" if vials_needed == 1 else "vials"
		return f"{vials_needed} ({vials_word}) {unit} ({total_volume:.1f} {vial_volume_uom})"
	except Exception:
		return ''


def get_prescription_coordinates(practitioner_doc, page_width, page_height):
	"""
	Get coordinate mapping for prescription fields.
	Can be customized per practitioner or use defaults.
	
	Args:
		practitioner_doc: Healthcare Practitioner document
		page_width: PDF page width in points
		page_height: PDF page height in points
		
	Returns:
		dict: Coordinate mapping for all fields
	"""
	# Try to get practitioner-specific coordinates
	try:
		from koraflow_core.utils.prescription_coordinates import get_practitioner_coordinates, get_default_coordinates
		custom_coords = get_practitioner_coordinates(practitioner_doc.name)
		if custom_coords:
			return custom_coords
		# Use default coordinates
		return get_default_coordinates(page_width, page_height)
	except ImportError:
		pass
	
	# Fallback default coordinates if module not available
	# NOTE: These coordinates are examples and need to be adjusted to match your PDF template layout
	# Coordinates are in PDF points (1 point = 1/72 inch), origin (0,0) at bottom-left
	return {
		'font_size': 10,
		# Patient information (adjust these to match your template)
		'patient_name': {'x': 50, 'y': page_height - 100, 'max_length': 50},
		'patient_id': {'x': 50, 'y': page_height - 120, 'max_length': 20},
		'patient_age': {'x': 300, 'y': page_height - 120, 'max_length': 10},
		'patient_gender': {'x': 400, 'y': page_height - 120, 'max_length': 10},
		
		# Practitioner information
		'practitioner_name': {'x': 50, 'y': page_height - 200, 'max_length': 50},
		'practice_number': {'x': 50, 'y': page_height - 220, 'max_length': 20},
		'hpcsa_registration': {'x': 300, 'y': page_height - 220, 'max_length': 20},
		
		# Date
		'date': {'x': 450, 'y': page_height - 100, 'max_length': 15},
		
		# Medications section
		'medications': {
			'y_start': page_height - 350,
			'x': 50,
			'line_height': 15,
			'max_items': 10,
			'name_x': 50,
			'name_max_length': 30,
			'dosage_x': 300,
			'dosage_max_length': 20,
			'instructions_x': 450,
			'instructions_max_length': 30
		}
	}


def get_prescription_data_for_overlay(encounter_doc, practitioner_doc):
	"""
	Extract prescription data in format suitable for PDF overlay.
	
	Args:
		encounter_doc: Patient Encounter document
		practitioner_doc: Healthcare Practitioner document
		
	Returns:
		dict: Data dictionary for overlay
	"""
	data = {}
	
	# Patient data
	if encounter_doc.patient:
		patient = frappe.get_doc("Patient", encounter_doc.patient)
		data['patient_name'] = patient.patient_name or patient.name
		data['patient_id'] = patient.uid or 'N/A'
		data['patient_dob'] = frappe.utils.formatdate(patient.dob) if patient.dob else ''
		data['patient_age'] = encounter_doc.patient_age or 'N/A'
		data['patient_gender'] = encounter_doc.patient_sex or 'N/A'

	# Practitioner data
	data['practitioner_name'] = practitioner_doc.practitioner_name or practitioner_doc.name
	data['hpcsa_registration'] = getattr(practitioner_doc, 'hpcsa_registration_number', None) or ''
	data['practice_number'] = getattr(practitioner_doc, 'practice_number', None) or ''
	data['practice_address'] = getattr(practitioner_doc, 'practice_address', None) or ''
	data['practitioner_phone'] = getattr(practitioner_doc, 'mobile_phone', '') or getattr(practitioner_doc, 'office_phone', '') or ''
	data['practitioner_email'] = getattr(practitioner_doc, 'email_id', '') or ''

	# Encounter data
	data['encounter_date'] = encounter_doc.encounter_date or frappe.utils.today()

	# Diagnosis and ICD-10 codes
	data['diagnosis'] = []
	if encounter_doc.diagnosis:
		for diag in encounter_doc.diagnosis:
			data['diagnosis'].append(diag.diagnosis)

	data['icd_codes'] = []
	if hasattr(encounter_doc, 'codification_table') and encounter_doc.codification_table:
		for code in encounter_doc.codification_table:
			data['icd_codes'].append({'code': code.code, 'description': code.code_value})
	
	# Medications - format for SAHPRA narrative prescription
	data['medications'] = []
	if encounter_doc.drug_prescription:
		for med in encounter_doc.drug_prescription:
			# Get medication name
			med_name = med.drug_name or med.medication or 'N/A'
			
			# Get strength
			strength_str = ''
			if med.strength:
				strength_str = f"{med.strength}"
				if med.strength_uom:
					strength_str += f" {med.strength_uom}"
			
			# Get dosage (from Prescription Dosage link)
			dosage_str = ''
			dosage_amount = None  # For quantity calculation
			dosage_uom = 'ml'  # Default UOM
			if med.dosage:
				try:
					dosage_doc = frappe.get_doc('Prescription Dosage', med.dosage)
					dosage_str = dosage_doc.dosage  # Use the dosage field value
					# Extract dosage amount from dosage_strength child table
					if hasattr(dosage_doc, 'dosage_strength') and dosage_doc.dosage_strength:
						for ds in dosage_doc.dosage_strength:
							if hasattr(ds, 'strength') and ds.strength:
								dosage_amount = float(ds.strength)
								if hasattr(ds, 'strength_uom') and ds.strength_uom:
									dosage_uom = str(ds.strength_uom)
								break
				except:
					dosage_str = str(med.dosage)
					# Try to parse dosage amount from string (e.g., "0.2 ml")
					import re
					match = re.search(r'(\d+\.?\d*)\s*(ml|mg|g)', str(med.dosage), re.IGNORECASE)
					if match:
						dosage_amount = float(match.group(1))
						dosage_uom = match.group(2).lower()
			
			# Get route from Item's route_of_administration field
			# First try drug_code, then medication's linked_items
			route = ''
			item_doc = None
			if hasattr(med, 'drug_code') and med.drug_code:
				try:
					item_doc = frappe.get_doc('Item', med.drug_code)
					route = getattr(item_doc, 'route_of_administration', '') or ''
				except:
					pass
			
			# If no route from drug_code, try medication's linked_items
			if not route and med.medication:
				try:
					medication_doc = frappe.get_doc('Medication', med.medication)
					if hasattr(medication_doc, 'linked_items') and medication_doc.linked_items:
						# Use first linked item
						linked_item_code = medication_doc.linked_items[0].item
						if linked_item_code:
							item_doc = frappe.get_doc('Item', linked_item_code)
							route = getattr(item_doc, 'route_of_administration', '') or ''
				except:
					pass
			
			# Get frequency from Medication's default_interval
			frequency = ''
			interval_days = 7  # Default to weekly
			if med.medication:
				try:
					medication_doc = frappe.get_doc('Medication', med.medication)
					if medication_doc.default_interval and medication_doc.default_interval_uom:
						interval = medication_doc.default_interval
						interval_uom = medication_doc.default_interval_uom.lower()
						interval_days = interval if interval_uom == 'day' else (interval * 7 if interval_uom == 'week' else interval)
						
						if interval_uom == 'day':
							if interval == 7:
								frequency = 'Once a week (7 days)'
							elif interval == 1:
								frequency = 'Once daily (1 day)'
							elif interval == 2:
								frequency = 'Twice daily (2 days)'
							else:
								frequency = f'Every {interval} days'
						elif interval_uom == 'hour':
							if interval == 1:
								frequency = 'Hourly'
							else:
								frequency = f'Every {interval} hours'
				except:
					pass
			
			# If frequency not found from medication, try from drug_prescription interval
			if not frequency and med.dosage_by_interval and med.interval and med.interval_uom:
				interval_uom_lower = med.interval_uom.lower()
				if interval_uom_lower == 'day':
					interval_days = med.interval
					if med.interval == 7:
						frequency = 'Once a week (7 days)'
					elif med.interval == 1:
						frequency = 'Once daily (1 day)'
					else:
						frequency = f'Every {med.interval} days'
				elif interval_uom_lower == 'week':
					interval_days = med.interval * 7
					if med.interval == 1:
						frequency = 'Once a week (7 days)'
					else:
						frequency = f'Every {med.interval} weeks'
			
			if not frequency:
				frequency = 'As directed'
			
			# Get duration (from period)
			duration = ''
			duration_days = None  # For quantity calculation
			if med.period:
				try:
					period_doc = frappe.get_doc('Prescription Duration', med.period)
					duration = period_doc.name
					# Get duration in days for calculation
					if hasattr(period_doc, 'get_days'):
						duration_days = period_doc.get_days()
					elif hasattr(period_doc, 'number') and hasattr(period_doc, 'period'):
						# Calculate days from number and period
						period_type = period_doc.period.lower()
						number = period_doc.number or 1
						if period_type == 'month':
							duration_days = number * 30
						elif period_type == 'week':
							duration_days = number * 7
						elif period_type == 'day':
							duration_days = number
						else:
							duration_days = number
				except:
					duration = str(med.period)
			
			# Calculate quantity: (dosage × number of doses) / vial size
			quantity = ''
			if item_doc and dosage_amount and duration_days:
				try:
					vial_volume = getattr(item_doc, 'volume', None)
					vial_volume_uom = getattr(item_doc, 'volume_uom', 'ml') or 'ml'
					
					if vial_volume:
						import math
						# Calculate number of doses based on interval
						# For weekly (7 days): calculate as weeks, not days
						if interval_days == 7:
							# Weekly dosing: calculate as number of weeks
							weeks = duration_days / 7
							doses = int(weeks)  # Exact number of weeks (e.g., 30 days = 4 weeks)
						else:
							# For other intervals, calculate based on days
							doses = int(duration_days / interval_days) if interval_days > 0 else 1
						
						# Ensure at least 1 dose
						if doses < 1:
							doses = 1
						
						# Calculate total volume needed
						total_volume = dosage_amount * doses
						
						# Calculate number of vials needed
						vials_needed = total_volume / vial_volume
						
						# Round up to nearest whole vial
						vials_needed = math.ceil(vials_needed)
						
						# Format quantity string: "1 vial (0.8 ml)"
						quantity = f"{int(vials_needed)} vial"
						if vials_needed > 1:
							quantity += "s"
						quantity += f" ({total_volume:.1f} {vial_volume_uom})"
				except Exception as e:
					frappe.logger().warning(f"Error calculating quantity for {med_name}: {str(e)}")
			
			# Get repeats
			repeats = 'As authorised'
			if med.number_of_repeats_allowed:
				if med.number_of_repeats_allowed == 0:
					repeats = 'No repeats'
				else:
					repeats = f"{int(med.number_of_repeats_allowed)} repeat(s)"
			
			med_data = {
				'name': med_name,
				'strength': strength_str,
				'dosage': dosage_str,
				'route': route,
				'frequency': frequency,
				'duration': duration,
				'quantity': quantity,
				'repeats': repeats,
				'comment': med.comment or ''  # Keep original comment for reference
			}
			data['medications'].append(med_data)
	
	return data


def attach_prescription_to_patient(pdf_content, patient, encounter):
	"""
	Attach prescription PDF to Patient Encounter (not Patient) to avoid showing in Patient attachments sidebar.
	The prescription will still be accessible via the Prescriptions link in the dashboard.
	
	Args:
		pdf_content: PDF content as bytes
		patient: Patient name or doc (for reference, not attachment)
		encounter: Patient Encounter name or doc (for filename reference and attachment)
		
	Returns:
		File: Created File document
	"""
	if isinstance(patient, str):
		patient_name = patient
	else:
		patient_name = patient.name
	
	if isinstance(encounter, str):
		encounter_name = encounter
		encounter_doc = frappe.get_doc("Patient Encounter", encounter)
	else:
		encounter_name = encounter.name
		encounter_doc = encounter
	
	# Generate filename - check if content is PDF or HTML
	encounter_date = formatdate(now(), "yyyy-MM-dd")
	# Check if content is PDF (starts with PDF magic bytes) or HTML
	if isinstance(pdf_content, bytes) and pdf_content.startswith(b'%PDF'):
		file_ext = ".pdf"
	else:
		file_ext = ".html"  # Fallback to HTML if PDF generation failed
	filename = f"Prescription_{encounter_name}_{encounter_date}{file_ext}"
	
	# Save file and attach to Patient Encounter (not Patient) to avoid showing in attachments sidebar
	try:
		# Ensure content is bytes
		if isinstance(pdf_content, str):
			content_bytes = pdf_content.encode('utf-8')
		else:
			content_bytes = pdf_content
		
		# Attach to Patient Encounter instead of Patient
		file_doc = save_file(
			fname=filename,
			content=content_bytes,
			dt="Patient Encounter",
			dn=encounter_name,
			folder="Home/Attachments",
			is_private=0,
			df=None
		)
		
		frappe.logger().info(f"Prescription PDF attached to Patient Encounter {encounter_name} (Patient: {patient_name}): {file_doc.file_url}")
		return file_doc
	except Exception as e:
		frappe.log_error(
			message=f"Error attaching prescription PDF to encounter {encounter_name}",
			title="Prescription Attachment Error"
		)
		frappe.throw(_("Failed to attach prescription PDF: {0}").format(str(e)))


def generate_and_attach_prescription(encounter):
	"""
	Complete workflow: Generate prescription PDF and attach to Patient Encounter.
	
	Args:
		encounter: Patient Encounter name or doc
		
	Returns:
		File: Created File document
	"""
	if isinstance(encounter, str):
		encounter_doc = frappe.get_doc("Patient Encounter", encounter)
	else:
		encounter_doc = encounter
	
	# Validate that encounter has medications
	if not encounter_doc.drug_prescription:
		frappe.logger().info(f"Encounter {encounter_doc.name} has no medications. Skipping prescription generation.")
		return None
	
	# Validate patient exists
	if not encounter_doc.patient:
		frappe.throw(_("No patient found in encounter. Cannot generate prescription."))
	
	# Generate PDF
	pdf_content = generate_prescription_pdf(encounter_doc)
	
	# Attach to patient
	file_doc = attach_prescription_to_patient(
		pdf_content=pdf_content,
		patient=encounter_doc.patient,
		encounter=encounter_doc
	)
	
	return file_doc
