// Copyright (c) 2024, KoraFlow Team and Contributors
// License: MIT. See LICENSE

frappe.ui.form.on('Patient Referral', {
	refresh: function(frm) {
		// Hide patient link from sales agents
		if (frappe.user.has_role('Sales Agent')) {
			frm.set_df_property('patient', 'hidden', 1);
			frm.set_df_property('internal_notes', 'hidden', 1);
		}
		
		// Add custom buttons
		if (!frm.is_new()) {
			// View referral detail button
			frm.add_custom_button(__('View Details'), function() {
				frappe.set_route('Form', 'Patient Referral', frm.doc.name);
			});
			
			// Send message to sales team (for agents)
			if (frappe.user.has_role('Sales Agent')) {
				frm.add_custom_button(__('Message Sales Team'), function() {
					frappe.prompt([
						{
							'fieldname': 'subject',
							'label': __('Subject'),
							'fieldtype': 'Data',
							'reqd': 1
						},
						{
							'fieldname': 'message',
							'label': __('Message'),
							'fieldtype': 'Text Editor',
							'reqd': 1
						}
					], function(values) {
						frappe.call({
							method: 'koraflow_core.koraflow_core.doctype.referral_message.referral_message.create_message',
							args: {
								referral: frm.doc.name,
								subject: values.subject,
								message: values.message
							},
							callback: function(r) {
								if (r.message) {
									frappe.show_alert({
										message: __('Message sent successfully'),
										indicator: 'green'
									});
									frm.reload_doc();
								}
							}
						});
					}, __('Send Message to Sales Team'));
				});
			}
		}
	},
	
	patient: function(frm) {
		// Auto-fetch patient name when patient is set
		if (frm.doc.patient) {
			frappe.call({
				method: 'koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.fetch_patient_names',
				args: {
					patient: frm.doc.patient
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('patient_first_name', r.message.first_name || '');
						frm.set_value('patient_last_name', r.message.last_name || '');
						frm.set_value('patient_name_display', r.message.patient_name || '');
					}
				}
			});
		}
	},
	
	sales_agent: function(frm) {
		// Auto-link Sales Partner when agent is set
		if (frm.doc.sales_agent && !frm.doc.sales_partner) {
			frappe.call({
				method: 'koraflow_core.koraflow_core.doctype.patient_referral.patient_referral.get_sales_partner_for_agent',
				args: {
					agent: frm.doc.sales_agent
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('sales_partner', r.message);
					}
				}
			});
		}
	}
});

