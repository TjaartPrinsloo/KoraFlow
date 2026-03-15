/**
 * Courier Guy Integration for Delivery Note
 * Adds waybill creation and tracking buttons to Delivery Note form
 */

frappe.ui.form.on('Delivery Note', {
	refresh: function (frm) {
		// Only show buttons if document is submitted
		if (frm.doc.docstatus === 1) {
			// Check if waybill already exists
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Courier Guy Waybill',
					filters: {
						delivery_note: frm.doc.name
					},
					limit: 1
				},
				callback: function (r) {
					if (r.message && r.message.length > 0) {
						// Waybill exists - show tracking and print buttons
						const waybill = r.message[0];

						frm.add_custom_button(__('View Waybill'), function () {
							frappe.set_route('Form', 'Courier Guy Waybill', waybill.name);
						}, __('Courier Guy'));

						if (waybill.tracking_number) {
							frm.add_custom_button(__('Update Tracking'), function () {
								frappe.call({
									method: 'koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.update_tracking_status',
									args: {
										waybill_name: waybill.name
									},
									callback: function (update_r) {
										if (update_r.message) {
											frappe.msgprint(__('Tracking updated. Status: {0}', [update_r.message]));
											frm.reload_doc();
										}
									}
								});
							}, __('Courier Guy'));

							frm.add_custom_button(__('Print Waybill'), function () {
								frappe.call({
									method: 'koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.get_waybill_print_url',
									args: {
										waybill_name: waybill.name
									},
									callback: function (print_r) {
										if (print_r.message) {
											window.open(print_r.message, '_blank');
										}
									}
								});
							}, __('Courier Guy'));

							// Show tracking status indicator
							if (waybill.status) {
								let indicator_color = 'blue';
								if (waybill.status === 'Delivered') {
									indicator_color = 'green';
								} else if (waybill.status === 'Failed' || waybill.status === 'Cancelled') {
									indicator_color = 'red';
								}

								frm.dashboard.add_indicator(
									__('Waybill Status: {0}', [waybill.status]),
									indicator_color
								);

								if (waybill.tracking_number) {
									frm.dashboard.add_indicator(
										__('Tracking: {0}', [waybill.tracking_number]),
										'blue'
									);
								}
							}
						}
					} else {
						// No waybill exists - show create button
						frm.add_custom_button(__('Create Courier Guy Waybill'), function () {
							frappe.confirm(
								__('Create a Courier Guy waybill for this delivery note?'),
								function () {
									// Yes
									frappe.call({
										method: 'koraflow_core.koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.create_waybill_from_delivery_note',
										args: {
											delivery_note: frm.doc.name
										},
										freeze: true,
										freeze_message: __('Creating waybill...'),
										callback: function (create_r) {
											if (create_r.message) {
												frappe.msgprint({
													title: __('Success'),
													message: __('Waybill created: {0}', [create_r.message]),
													indicator: 'green'
												});
												frm.reload_doc();
											}
										},
										error: function (r) {
											frappe.msgprint({
												title: __('Error'),
												message: r.message || __('Failed to create waybill'),
												indicator: 'red'
											});
										}
									});
								},
								function () {
									// No - do nothing
								}
							);
						}, __('Courier Guy'));
					}
				}
			});
		}
	}
});

