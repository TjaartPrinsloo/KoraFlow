// Custom User form enhancements for KoraFlow
frappe.ui.form.on("User", {
	refresh: function(frm) {
		// Ensure intake_completed field displays correctly
		// Force refresh the field value if it exists
		if (!frm.is_new() && frm.fields_dict.intake_completed) {
			// Get the current value from the document
			let intake_value = frm.doc.intake_completed;
			// Set the field value explicitly to ensure checkbox is checked/unchecked
			if (intake_value !== undefined) {
				frm.set_value("intake_completed", intake_value ? 1 : 0);
				// Also update the checkbox directly
				let checkbox_field = frm.fields_dict.intake_completed;
				if (checkbox_field && checkbox_field.$input) {
					checkbox_field.$input.prop("checked", intake_value ? true : false);
				}
			}
		}
		
		// Add Force Verify Email button for admins
		if (!frm.is_new() && frm.doc.email && !frm.doc.email_verified) {
			if (frappe.user.has_role("System Manager") || frappe.user.has_role("Healthcare Administrator")) {
				frm.add_custom_button(
					__("Force Verify Email"),
					function() {
						// Show dialog to get reason (optional)
						let d = new frappe.ui.Dialog({
							title: __("Force Verify Email"),
							fields: [
								{
									label: __("Reason (Optional)"),
									fieldname: "reason",
									fieldtype: "Small Text",
									description: __("Reason for force verification (e.g., 'Patient cannot access email', 'Assisted signup')")
								}
							],
							primary_action_label: __("Verify"),
							primary_action(values) {
								frappe.call({
									method: "koraflow_core.api.patient_signup.force_verify_email",
									args: {
										user_email: frm.doc.name,
										reason: values.reason || null
									},
									callback: function(r) {
										if (r.message) {
											frappe.show_alert({
												message: r.message,
												indicator: "green"
											}, 5);
											frm.reload_doc();
										}
									}
								});
								d.hide();
							}
						});
						d.show();
					},
					__("Verification")
				);
			}
		}
		
		// Show verification status
		if (!frm.is_new() && frm.doc.email_verified) {
			let verified_via = frm.doc.email_verified_via || "Email";
			let verified_on = frm.doc.email_verified_on ? frappe.datetime.str_to_user(frm.doc.email_verified_on) : "";
			let verified_by = frm.doc.email_verified_by || "";
			
			let status_msg = __("Email Verified");
			if (verified_via === "Admin" && verified_by) {
				status_msg += ` (${__("by")} ${verified_by})`;
			}
			if (verified_on) {
				status_msg += ` - ${verified_on}`;
			}
			
			frm.dashboard.add_indicator(status_msg, "green");
		}
		
		// Show intake completion status
		if (!frm.is_new() && frm.doc.intake_completed !== undefined) {
			if (!frm.doc.intake_completed) {
				frm.dashboard.add_indicator(__("Intake form not completed"), "orange");
			} else {
				frm.dashboard.add_indicator(__("Intake form completed"), "green");
			}
		}
	},
	
	// Also handle onload to ensure field is set correctly when form loads
	onload: function(frm) {
		// Ensure intake_completed field is properly displayed
		if (!frm.is_new() && frm.fields_dict.intake_completed) {
			// Small delay to ensure form is fully loaded
			setTimeout(function() {
				let intake_value = frm.doc.intake_completed;
				if (intake_value !== undefined && frm.fields_dict.intake_completed) {
					frm.set_value("intake_completed", intake_value ? 1 : 0);
					let checkbox_field = frm.fields_dict.intake_completed;
					if (checkbox_field && checkbox_field.$input) {
						checkbox_field.$input.prop("checked", intake_value ? true : false);
					}
				}
			}, 100);
		}
	}
});

