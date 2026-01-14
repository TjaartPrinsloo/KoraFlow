// Copyright (c) 2025, KoraFlow Team and Contributors
// License: MIT. See LICENSE

/**
 * GLP-1 Pharmacist Dashboard
 * Queue of pending dispense tasks with batch selection and cold chain validation
 */

frappe.pages['glp1-pharmacist-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('GLP-1 Pharmacist Dashboard'),
		single_column: true
	});
	
	// Add refresh button
	page.add_inner_button(__('Refresh'), function() {
		refresh_dashboard();
	});
	
	// Load dashboard
	load_dashboard(page);
};

function load_dashboard(page) {
	frappe.call({
		method: 'koraflow_core.api.glp1_pharmacist.get_dispense_queue',
		callback: function(r) {
			if (r.message) {
				render_dashboard(page, r.message);
			}
		}
	});
}

function render_dashboard(page, data) {
	// Clear existing content
	page.main.empty();
	
	// Create queue table
	var $table = $('<div class="dispense-queue"></div>');
	
	if (data.tasks && data.tasks.length > 0) {
		data.tasks.forEach(function(task) {
			var $task_row = create_task_row(task);
			$table.append($task_row);
		});
	} else {
		$table.append($('<div class="text-muted">No pending dispense tasks</div>'));
	}
	
	page.main.append($table);
}

function create_task_row(task) {
	var $row = $(`
		<div class="task-row" data-task="${task.name}">
			<div class="task-header">
				<h4>${task.patient_name || task.patient}</h4>
				<span class="badge badge-primary">${task.status}</span>
			</div>
			<div class="task-details">
				<p><strong>Prescription:</strong> ${task.prescription}</p>
				<p><strong>Allocation:</strong> ${task.allocated_quantity || 'N/A'}</p>
			</div>
			<div class="batch-selection">
				<h5>Available Batches</h5>
				<div class="batch-list"></div>
			</div>
			<div class="task-actions">
				<button class="btn btn-primary btn-sm start-dispense" data-task="${task.name}">
					Start Dispense
				</button>
			</div>
		</div>
	`);
	
	// Load batch availability
	if (task.batch_availability && task.batch_availability.length > 0) {
		task.batch_availability.forEach(function(batch) {
			var $batch_item = $(`
				<div class="batch-item" data-batch="${batch.batch}">
					<span>Batch: ${batch.batch}</span>
					<span>Expiry: ${batch.expiry_date || 'N/A'}</span>
					<span>Available: ${batch.available_quantity || 0}</span>
					<button class="btn btn-sm btn-secondary select-batch" data-batch="${batch.batch}">
						Select
					</button>
				</div>
			`);
			$row.find('.batch-list').append($batch_item);
		});
	}
	
	// Bind events
	$row.find('.start-dispense').on('click', function() {
		start_dispense(task.name);
	});
	
	$row.find('.select-batch').on('click', function() {
		var batch = $(this).data('batch');
		select_batch(task.name, batch);
	});
	
	return $row;
}

function start_dispense(task_name) {
	frappe.prompt([
		{
			fieldname: 'batch',
			fieldtype: 'Link',
			label: 'Batch',
			options: 'Batch',
			reqd: 1
		},
		{
			fieldname: 'quantity',
			fieldtype: 'Float',
			label: 'Quantity',
			reqd: 1
		},
		{
			fieldname: 'patient_acknowledged',
			fieldtype: 'Check',
			label: 'Patient Acknowledged',
			reqd: 1
		},
		{
			fieldname: 'counseling_notes',
			fieldtype: 'Text Editor',
			label: 'Counseling Notes'
		}
	], function(values) {
		frappe.call({
			method: 'koraflow_core.api.glp1_pharmacist.create_dispense',
			args: {
				task: task_name,
				batch: values.batch,
				quantity: values.quantity,
				patient_acknowledged: values.patient_acknowledged,
				counseling_notes: values.counseling_notes
			},
			callback: function(r) {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: __('Dispense created successfully'),
						indicator: 'green'
					});
					refresh_dashboard();
				}
			}
		});
	}, __('Create Dispense'), __('Create'));
}

function select_batch(task_name, batch) {
	// Validate cold chain
	frappe.call({
		method: 'koraflow_core.utils.glp1_compliance.check_cold_chain_compliance',
		args: { batch: batch },
		callback: function(r) {
			if (r.message && !r.message.compliant) {
				frappe.msgprint({
					title: __('Cold Chain Issue'),
					message: __('Unresolved temperature excursions exist for this batch. Cannot dispense.'),
					indicator: 'red'
				});
			} else {
				frappe.show_alert({
					message: __('Batch selected: {0}', [batch]),
					indicator: 'green'
				});
			}
		}
	});
}

function refresh_dashboard() {
	frappe.set_route('glp1-pharmacist-dashboard');
}
