// Copyright (c) 2024, KoraFlow Team and Contributors
// License: MIT. See LICENSE

frappe.ui.form.on('Commission Record', {
	refresh: function(frm) {
		// All fields are read-only for sales agents
		if (frappe.user.has_role('Sales Agent')) {
			frm.set_read_only();
		}
		
		// Add link to referral
		if (frm.doc.referral) {
			frm.add_custom_button(__('View Referral'), function() {
				frappe.set_route('Form', 'Patient Referral', frm.doc.referral);
			});
		}
	}
});

