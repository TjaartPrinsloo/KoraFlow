// Copyright (c) 2025, KoraFlow Team and Contributors
// License: MIT. See LICENSE

/**
 * GLP-1 Doctor Prescription Interface
 * Prescription creation with contraindication warnings
 */

frappe.ui.form.on('GLP-1 Patient Prescription', {
	refresh: function(frm) {
		// Add contraindication check
		if (frm.doc.patient && frm.doc.medication) {
			check_contraindications(frm);
		}
		
		// Add dosage calculator
		if (frm.doc.patient) {
			add_dosage_calculator(frm);
		}
	},
	
	patient: function(frm) {
		if (frm.doc.patient) {
			load_patient_intake(frm);
		}
	},
	
	medication: function(frm) {
		if (frm.doc.medication) {
			check_contraindications(frm);
		}
	}
});

function check_contraindications(frm) {
	frappe.call({
		method: 'koraflow_core.api.glp1_doctor.check_contraindications',
		args: {
			patient: frm.doc.patient,
			medication: frm.doc.medication
		},
		callback: function(r) {
			if (r.message && r.message.contraindications) {
				var warnings = r.message.contraindications;
				if (warnings.length > 0) {
					frappe.msgprint({
						title: __('Contraindication Warnings'),
						message: warnings.join('<br>'),
						indicator: 'orange'
					});
				}
			}
		}
	});
}

function load_patient_intake(frm) {
	frappe.call({
		method: 'koraflow_core.api.glp1_doctor.get_patient_intake',
		args: {
			patient: frm.doc.patient
		},
		callback: function(r) {
			if (r.message && r.message.intake) {
				// Show intake data in a dialog or form section
				show_intake_data(frm, r.message.intake);
			}
		}
	});
}

function add_dosage_calculator(frm) {
	if (!frm.doc.medication) return;
	
	frm.add_custom_button(__('Dosage Calculator'), function() {
		frappe.prompt([
			{
				fieldname: 'patient_weight',
				fieldtype: 'Float',
				label: 'Patient Weight (kg)',
				reqd: 1
			},
			{
				fieldname: 'starting_dose',
				fieldtype: 'Select',
				label: 'Starting Dose',
				options: '\n0.25mg\n0.5mg\n1.0mg\n2.5mg\n5.0mg',
				reqd: 1
			}
		], function(values) {
			// Calculate recommended dosage
			var recommended = calculate_dosage(values.patient_weight, values.starting_dose);
			frappe.msgprint({
				title: __('Recommended Dosage'),
				message: __('Recommended starting dosage: {0}', [recommended]),
				indicator: 'blue'
			});
			
			if (!frm.doc.dosage) {
				frm.set_value('dosage', recommended);
			}
		}, __('Dosage Calculator'), __('Calculate'));
	});
}

function calculate_dosage(weight, starting_dose) {
	// Simplified dosage calculation - adjust based on clinical guidelines
	var base_dose = parseFloat(starting_dose) || 0.25;
	
	// Adjust based on weight (simplified)
	if (weight > 100) {
		base_dose = base_dose * 1.2;
	} else if (weight < 60) {
		base_dose = base_dose * 0.8;
	}
	
	return base_dose.toFixed(2) + 'mg';
}

function show_intake_data(frm, intake) {
	// Create a dialog to show intake data
	var dialog = new frappe.ui.Dialog({
		title: __('Patient Intake Data'),
		fields: [
			{
				fieldtype: 'HTML',
				options: '<div class="intake-data">' + 
					'<p><strong>BMI:</strong> ' + (intake.calculated_bmi || 'N/A') + '</p>' +
					'<p><strong>Contraindications:</strong> ' + (intake.has_contraindications ? 'Yes' : 'No') + '</p>' +
					'</div>'
			}
		]
	});
	dialog.show();
}
