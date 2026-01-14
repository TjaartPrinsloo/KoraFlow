"""
Prescription Coordinate Configuration
Configure text overlay coordinates for PDF template filling
"""
import frappe


def get_practitioner_coordinates(practitioner_name):
	"""
	Get coordinate mapping for a specific practitioner.
	Can be customized per practitioner via Custom Field or DocType.
	
	Args:
		practitioner_name: Healthcare Practitioner name
		
	Returns:
		dict: Coordinate mapping or None to use defaults
	"""
	# Check if practitioner has custom coordinates stored
	# This could be in a custom field or separate DocType
	# For now, return None to use defaults
	return None


def get_default_coordinates(page_width, page_height):
	"""
	Get coordinate mapping for Slim 2 Well prescription template.
	Coordinates are in PDF points (1 point = 1/72 inch).
	Origin (0,0) is at bottom-left corner.
	
	Based on the Slim 2 Well prescription template layout:
	- Practitioner details are already on the template (no overlay needed)
	- Only need to fill:
	  1. Patient name in "Patient Name:" placeholder
	  2. Date in "Date:" placeholder  
	  3. Medications in empty space below (name, dosage, amount, prescription length)
	
	Args:
		page_width: PDF page width in points (typically 595 for A4)
		page_height: PDF page height in points (typically 842 for A4)
		
	Returns:
		dict: Coordinate mapping for all fields
	"""
	# A4 dimensions: 595 x 842 points
	# Based on template analysis - placeholders are in middle section
	
	return {
		'font_size': 10,
		'font_name': 'Helvetica',
		
		# MIDDLE SECTION - Patient Name and Date Placeholders
		# These placeholders appear in the middle of the page, after addresses
		# "Patient Name:" placeholder text is at left, patient name should be NEXT TO it (same Y, offset X)
		# Placeholder text "Patient Name:" ends around x=150-180, so patient name starts at x=180-200
		'patient_name_placeholder': {'x': 180, 'y': page_height - 372, 'max_length': 50, 'font_size': 14},
		
		# "Date:" placeholder text is at right, date should be NEXT TO it (same Y, offset X)
		# Placeholder text "Date:" ends around x=380-400, so date starts at x=400-420
		'date_placeholder': {'x': 480, 'y': page_height - 372, 'max_length': 20, 'font_size': 14},
		
		# MEDICATION SECTION - Empty space below patient name and date
		# SAHPRA Narrative Format - multi-line format for each medication
		'medications': {
			'y_start': page_height - 450,  # Start below the placeholders
			'x': 50,
			'line_height': 12,  # Line height for each detail line
			'medication_spacing': 20,  # Space between different medications
			'max_items': 5,  # Fewer items since each takes more space
			'font_size': 9,  # Font size for medication details
			'name_font_size': 10  # Font size for medication name (slightly larger)
		}
	}
