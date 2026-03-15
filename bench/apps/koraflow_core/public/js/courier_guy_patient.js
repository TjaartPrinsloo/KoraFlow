/**
 * Courier Guy Patient Tracking Integration
 * Adds waybill tracking section to Patient form
 */

frappe.ui.form.on('Patient', {
	refresh: function (frm) {
		// Add Courier Guy tracking section
		if (frm.doc.name) {
			frappe.call({
				method: 'koraflow_core.api.courier_guy_tracking.get_patient_tracking',
				args: {
					patient_name: frm.doc.name
				},
				callback: function (r) {
					if (r.message && r.message.success && r.message.waybills.length > 0) {
						// Create dashboard section
						const waybills = r.message.waybills;

						// Add section to dashboard
						frm.dashboard.add_section(
							__('Courier Guy Shipments'),
							waybills.map(wb => ({
								label: __('Waybill {0}', [wb.waybill_number || wb.tracking_number]),
								value: wb.status,
								indicator: get_status_indicator(wb.status),
								action: function () {
									frappe.set_route('Form', 'Courier Guy Waybill', wb.name);
								}
							}))
						);

						// Add tracking details
						waybills.forEach(wb => {
							if (wb.tracking_number) {
								frm.dashboard.add_indicator(
									__('Tracking: {0} - {1}', [wb.tracking_number, wb.status]),
									get_status_indicator(wb.status)
								);
							}
						});
					}
				}
			});
		}
	}
});

function get_status_indicator(status) {
	const status_map = {
		'Delivered': 'green',
		'In Transit': 'blue',
		'Created': 'orange',
		'Failed': 'red',
		'Cancelled': 'red',
		'Draft': 'gray'
	};
	return status_map[status] || 'blue';
}

