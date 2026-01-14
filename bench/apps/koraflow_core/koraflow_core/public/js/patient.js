// Patient Prescriptions Integration
// Adds prescription shortcut to Patient dashboard in "Appointments and Encounters" section

// Only run if we're on a Patient form
if (frappe && frappe.ui && frappe.ui.form) {
	console.log('🔵 KoraFlow Patient JS loaded!');

	frappe.ui.form.on('Patient', {
	refresh: function(frm) {
		// Add prescription link to form links section in "Appointments and Encounters" group
		if (frm.doc.name && !frm.is_new()) {
			console.log('Patient form refresh - adding prescription link for:', frm.doc.name);
			
			// Function to add prescription link to the section
			function addPrescriptionLink(count, prescriptions) {
				console.log('addPrescriptionLink called with count:', count);
				
				// Wait for dashboard to be ready - try multiple times
				let attempts = 0;
				const maxAttempts = 15;
				
				function tryAdd() {
					attempts++;
					console.log('Attempt', attempts, 'to find Appointments and Encounters section');
					
					// Try to find the form links area - multiple selectors
					let formLinksArea = $('.form-documents');
					if (!formLinksArea.length) {
						formLinksArea = $('.form-dashboard-section.form-links');
					}
					if (!formLinksArea.length) {
						formLinksArea = frm.dashboard ? frm.dashboard.transactions_area : null;
					}
					
					if (!formLinksArea || !formLinksArea.length) {
						if (attempts < maxAttempts) {
							setTimeout(tryAdd, 300);
							return;
						}
						console.warn('Could not find form-documents area after', maxAttempts, 'attempts');
						return;
					}
					
					console.log('Found form links area, looking for Appointments section...');
					
					// Find the section that contains "Patient Encounter"
					let appointmentsSection = null;
					
					// Method 1: Find by Patient Encounter link
					formLinksArea.find('.document-link').each(function() {
						if ($(this).attr('data-doctype') === 'Patient Encounter') {
							appointmentsSection = $(this).closest('.col-md-4');
							console.log('Found section via Patient Encounter link');
							return false; // break
						}
					});
					
					// Method 2: Find by title text
					if (!appointmentsSection || !appointmentsSection.length) {
						formLinksArea.find('.form-link-title').each(function() {
							const text = $(this).text().trim();
							console.log('Checking title:', text);
							if (text.includes('Appointments') || text.includes('Encounters') || 
							    text === 'Appointments and Encounters') {
								appointmentsSection = $(this).closest('.col-md-4');
								console.log('Found section via title');
								return false;
							}
						});
					}
					
					if (appointmentsSection && appointmentsSection.length) {
						console.log('Found Appointments section, adding Prescriptions link...');
						
						// Check if Prescriptions link already exists
						if (!appointmentsSection.find('.document-link[data-prescription-link="true"]').length) {
							// Create the prescription link element matching the format of other links
							const prescriptionLink = $(`
								<div class="document-link" data-prescription-link="true">
									<div class="document-link-badge">
										<span class="count ${count > 0 ? '' : 'hidden'}">${count > 0 ? count : ''}</span>
										<a class="badge-link" style="cursor: pointer;">${__('Prescriptions')}</a>
									</div>
								</div>
							`);
							
							// Add it after Patient Encounter link (or last link in section)
							const patientEncounterLink = appointmentsSection.find('.document-link[data-doctype="Patient Encounter"]');
							if (patientEncounterLink.length) {
								patientEncounterLink.after(prescriptionLink);
								console.log('Added Prescriptions link after Patient Encounter');
							} else {
								appointmentsSection.find('.document-link').last().after(prescriptionLink);
								console.log('Added Prescriptions link at end of section');
							}
							
							// Bind click event - show prescriptions in a dialog
							prescriptionLink.find('.badge-link').on('click', function(e) {
								e.preventDefault();
								showPrescriptionsDialog(frm, prescriptions || []);
							});
							
							console.log('✓ Prescriptions link added successfully with count:', count);
						} else {
							console.log('Prescriptions link already exists, updating count...');
							// Update count if link already exists
							const existingLink = appointmentsSection.find('.document-link[data-prescription-link="true"]');
							const countSpan = existingLink.find('.count');
							if (count > 0) {
								countSpan.text(count).removeClass('hidden');
							} else {
								countSpan.addClass('hidden');
							}
							
							// Update click handler with new prescriptions data
							existingLink.find('.badge-link').off('click').on('click', function(e) {
								e.preventDefault();
								showPrescriptionsDialog(frm, prescriptions || []);
							});
						}
					} else if (attempts < maxAttempts) {
						// Retry if section not found yet
						setTimeout(tryAdd, 300);
					} else {
						console.error('Could not find Appointments and Encounters section after', maxAttempts, 'attempts');
						console.log('Available sections:', formLinksArea.find('.form-link-title').map(function() {
							return $(this).text().trim();
						}).get());
					}
				}
				
				// Start trying after a short delay to ensure DOM is ready
				setTimeout(tryAdd, 800);
			}
			
			// Get prescriptions
			frappe.call({
				method: 'koraflow_core.api.patient_prescriptions.get_patient_prescriptions',
				args: {
					patient: frm.doc.name
				},
				callback: function(r) {
					if (r.exc) {
						console.error('Error getting prescriptions:', r.exc);
						addPrescriptionLink(0, []);
					} else {
						const count = r.message ? (r.message.count || 0) : 0;
						const prescriptions = r.message ? (r.message.prescriptions || []) : [];
						console.log('Got prescriptions:', count, 'total');
						addPrescriptionLink(count, prescriptions);
					}
				},
				error: function(r) {
					console.error('API call failed:', r);
					// If API call fails, still add the link without count
					addPrescriptionLink(0, []);
				}
			});
		}
	}
	});
}

// Function to show prescriptions in a dialog
function showPrescriptionsDialog(frm, prescriptions) {
	if (!prescriptions || prescriptions.length === 0) {
		frappe.msgprint({
			title: __('Prescriptions'),
			message: __('No prescriptions found for this patient.'),
			indicator: 'blue'
		});
		return;
	}
	
	// Create dialog content
	let content = `
		<div class="prescriptions-dialog">
			<div class="prescriptions-header">
				<h5>${__('All Prescriptions')} (${prescriptions.length})</h5>
			</div>
			<div class="prescriptions-list" style="max-height: 500px; overflow-y: auto;">
	`;
	
	prescriptions.forEach(function(prescription) {
		const fileName = prescription.file_name || 'Unknown';
		const encounter = prescription.encounter ? ` - ${prescription.encounter}` : '';
		const created = prescription.creation ? frappe.datetime.str_to_user(prescription.creation) : '';
		
		content += `
			<div class="prescription-item" style="padding: 10px; border-bottom: 1px solid #dee2e6;">
				<div style="display: flex; justify-content: space-between; align-items: center;">
					<div>
						<strong>${fileName}</strong>
						${encounter ? `<br><small class="text-muted">${__('Encounter')}: ${encounter}</small>` : ''}
						${created ? `<br><small class="text-muted">${__('Created')}: ${created}</small>` : ''}
					</div>
					<div>
						<a href="${prescription.file_url}" target="_blank" class="btn btn-sm btn-primary">
							${__('View/Download')}
						</a>
					</div>
				</div>
			</div>
		`;
	});
	
	content += `
			</div>
		</div>
	`;
	
	// Show dialog
	const dialog = new frappe.ui.Dialog({
		title: __('Prescriptions - {0}', [frm.doc.patient_name || frm.doc.name]),
		fields: [
			{
				fieldtype: 'HTML',
				options: content
			}
		],
		primary_action_label: __('Close'),
		primary_action: function() {
			dialog.hide();
		}
	});
	
	dialog.show();
}
