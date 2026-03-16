// Copyright (c) 2024, KoraFlow Team and Contributors
// License: MIT. See LICENSE

frappe.ui.form.on('Referral Message', {
	refresh: function(frm) {
		// Mark as read when opened
		if (frm.doc.status === "Unread" && frm.doc.to_user === frappe.session.user) {
			frm.set_value('status', 'Read');
			frm.save();
		}
	}
});

