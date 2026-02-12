frappe.ui.form.on('Courier Guy Waybill', {
	refresh: function (frm) {
		// Add custom buttons
		if (frm.doc.status === 'Created' && frm.doc.tracking_number) {
			frm.add_custom_button(__('Update Tracking'), function () {
				frappe.call({
					method: 'koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.update_tracking_status',
					args: {
						waybill_name: frm.doc.name
					},
					callback: function (r) {
						if (r.message) {
							frappe.msgprint(__('Tracking updated. Status: {0}', [r.message]));
							frm.reload_doc();
						}
					}
				});
			}, __('Actions'));

			frm.add_custom_button(__('Print Waybill'), function () {
				frappe.call({
					method: 'koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.get_waybill_print_url',
					args: {
						waybill_name: frm.doc.name
					},
					callback: function (r) {
						if (r.message) {
							window.open(r.message, '_blank');
						}
					}
				});
			}, __('Actions'));
		}

		// Show tracking history if available
		if (frm.doc.tracking_history) {
			try {
				const history = JSON.parse(frm.doc.tracking_history);
				if (history && history.length > 0) {
					frm.dashboard.add_section(
						__('Tracking History'),
						history.map(item => ({
							label: item.status || item.description || 'Update',
							value: item.timestamp || item.date || '',
							indicator: item.status === 'Delivered' ? 'green' : 'blue'
						}))
					);
				}
			} catch (e) {
				// Ignore parse errors
			}
		}
	},

	delivery_note: function (frm) {
		// Auto-populate from delivery note
		if (frm.doc.delivery_note) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Delivery Note',
					name: frm.doc.delivery_note
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value('customer', r.message.customer);

						// Try to find patient
						if (r.message.customer) {
							frappe.call({
								method: 'frappe.client.get_list',
								args: {
									doctype: 'Patient',
									filters: {
										customer: r.message.customer
									},
									limit: 1
								},
								callback: function (patient_r) {
									if (patient_r.message && patient_r.message.length > 0) {
										frm.set_value('patient', patient_r.message[0].name);
									}
								}
							});
						}
					}
				}
			});
		}
	}
});

