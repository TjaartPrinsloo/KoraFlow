/**
 * Courier Guy Dashboard
 * Fetches real-time data from Courier Guy API and displays it
 * Version: 2.0 - Fixed null route errors
 */

// Wrap everything in IIFE to ensure proper initialization
(function () {
	'use strict';

	// Wait for dependencies and initialize
	function initDashboard() {
		if (typeof frappe === 'undefined') {
			setTimeout(initDashboard, 100);
			return;
		}

		// Create namespace
		frappe.provide('koraflow_core.courier_guy');

		if (typeof koraflow_core === 'undefined' || typeof koraflow_core.courier_guy === 'undefined') {
			setTimeout(initDashboard, 100);
			return;
		}

		// Define Dashboard class if not already defined
		if (!koraflow_core.courier_guy.Dashboard) {
			koraflow_core.courier_guy.Dashboard = class CourierGuyDashboard {
				constructor() {
					this.currentPage = 1;
					this.itemsPerPage = 50;
					this.allShipments = [];
					this.init();
				}

				init() {
					this.setup_custom_block();
				}

				setup_custom_block() {
					// URL-only workspace detection (no content sniffing to avoid false positives)
					const isCourierGuyWorkspace = () => {
						try {
							// Method 1: Check frappe route (most reliable in SPA)
							if (typeof frappe !== 'undefined' && frappe.get_route && typeof frappe.get_route === 'function') {
								try {
									const route = frappe.get_route();
									if (route && Array.isArray(route) && route.length >= 2) {
										const routeStr = route.map(r => String(r).toLowerCase().trim()).join('/');
										if (routeStr.includes('workspace') && (
											routeStr.includes('courier-guy') ||
											routeStr.includes('courier guy') ||
											routeStr.includes('courier_guy')
										)) {
											return true;
										}
									}
								} catch (e) { /* ignore */ }
							}
							// Method 2: Check URL hash and pathname
							const url = window.location.href.toLowerCase();
							const hash = (window.location.hash || '').toLowerCase();
							if (hash.includes('workspace') && (
								hash.includes('courier-guy') || hash.includes('courier%20guy') || hash.includes('courier_guy')
							)) {
								return true;
							}
							const pathname = window.location.pathname.toLowerCase();
							if (pathname.includes('/app/courier-guy') || pathname.includes('/app/courier_guy')) {
								return true;
							}
							return false;
						} catch (e) {
							return false;
						}
					};

					// Listen for route changes
					const setupRouter = () => {
						if (typeof frappe !== 'undefined' && frappe.router && typeof frappe.router.on === 'function') {
							frappe.router.on('change', () => {
								if (isCourierGuyWorkspace() && !document.querySelector('.courier-guy-api-dashboard')) {
									setTimeout(() => this.load_dashboard_data(), 1000);
								}
							});
						} else {
							setTimeout(setupRouter, 500);
						}
					};
					if (typeof frappe !== 'undefined') {
						setupRouter();
					}

					// Check on initial page load (once)
					setTimeout(() => {
						if (isCourierGuyWorkspace() && !document.querySelector('.courier-guy-api-dashboard')) {
							this.load_dashboard_data();
						}
					}, 1500);
				}


				async load_dashboard_data() {
					// Route guard: only render on Courier Guy workspace
					const pathname = window.location.pathname.toLowerCase();
					const hash = (window.location.hash || '').toLowerCase();
					const onCourierGuyPage = (
						pathname.includes('/app/courier-guy') || pathname.includes('/app/courier_guy') ||
						(hash.includes('workspace') && (hash.includes('courier-guy') || hash.includes('courier%20guy') || hash.includes('courier_guy')))
					);
					if (!onCourierGuyPage) {
						return;
					}

					// Check if dashboard already loaded
					if (document.querySelector('.courier-guy-api-dashboard')) {
						return;
					}

					// Target the exact element from the DOM path provided: .layout-main-section
					// Try multiple selectors to find the workspace content area
					let dashboard_container =
						document.querySelector('.layout-main-section') ||
						document.querySelector('.col.layout-main-section-wrapper .layout-main-section') ||
						document.querySelector('.codex-editor') ||
						document.querySelector('#editorjs') ||
						document.querySelector('.editor-js-container') ||
						document.querySelector('[data-workspace="Courier Guy"]') ||
						document.querySelector('.workspace-content') ||
						document.querySelector('#page-Workspaces .page-content') ||
						document.querySelector('.page-content') ||
						document.querySelector('.main-section');

					if (!dashboard_container) {
						console.error('  Tried selectors: .layout-main-section, .codex-editor, #editorjs, etc.');
						console.error('  Available elements:', {
							layoutMainSection: !!document.querySelector('.layout-main-section'),
							codexEditor: !!document.querySelector('.codex-editor'),
							editorJs: !!document.querySelector('#editorjs'),
							pageContent: !!document.querySelector('.page-content'),
							body: !!document.querySelector('#body')
						});
						setTimeout(() => this.load_dashboard_data(), 1000);
						return;
					}


					// Create dashboard container
					const api_dashboard = document.createElement('div');
					api_dashboard.className = 'courier-guy-api-dashboard';

					// Set default date range (last 1 week)
					const today = new Date();
					const oneWeekAgo = new Date(today);
					oneWeekAgo.setDate(today.getDate() - 7);

					const formatDate = (date) => {
						const year = date.getFullYear();
						const month = String(date.getMonth() + 1).padStart(2, '0');
						const day = String(date.getDate()).padStart(2, '0');
						return `${year}-${month}-${day}`;
					};

					// Format dates before using in template (pre-format to avoid scope issues)
					let fromDateStr, toDateStr;
					try {
						fromDateStr = formatDate(oneWeekAgo);
						toDateStr = formatDate(today);
					} catch (e) {
						// Fallback to hardcoded dates if formatting fails
						const today_fallback = new Date();
						const oneWeekAgo_fallback = new Date(today_fallback);
						oneWeekAgo_fallback.setDate(today_fallback.getDate() - 7);
						fromDateStr = formatDate(oneWeekAgo_fallback);
						toDateStr = formatDate(today_fallback);
					}

					api_dashboard.innerHTML = `
						<div class="dashboard-header">
							<h4>Courier Guy Live Dashboard</h4>
							<div class="dashboard-actions">
								<button class="btn btn-sm btn-secondary refresh-dashboard" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.refresh(); }">
									<i class="fa fa-refresh"></i> Refresh
								</button>
							</div>
						</div>
						<div class="dashboard-api-warning" style="display: none; margin: 10px 0; padding: 10px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; color: #856404;">
							<i class="fa fa-exclamation-triangle"></i> <span class="warning-message"></span>
						</div>
						<div class="dashboard-filters">
							<div class="filter-group">
								<label>From:</label>
								<input type="date" class="form-control date-filter" id="dashboard-from-date" value="${fromDateStr}">
							</div>
							<div class="filter-group">
								<label>To:</label>
								<input type="date" class="form-control date-filter" id="dashboard-to-date" value="${toDateStr}">
							</div>
							<button class="btn btn-sm btn-primary apply-filters" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.applyFilters(); }">
								Apply
							</button>
						</div>
						<div class="dashboard-loading" style="display: none;">
							<i class="fa fa-spinner fa-spin"></i> Loading dashboard data...
						</div>
						<div class="dashboard-prompt" style="text-align: center; padding: 20px; color: #888;">
							Select a date range and click <strong>Apply</strong> to load shipment data.
						</div>
						<div class="dashboard-content" style="display: none;">
							<div class="dashboard-summary">
								<div class="summary-card created">
									<div class="summary-label">Created</div>
									<div class="summary-value" id="summary-created">0</div>
								</div>
								<div class="summary-card collected">
									<div class="summary-label">Collected</div>
									<div class="summary-value" id="summary-collected">0</div>
								</div>
								<div class="summary-card delivered">
									<div class="summary-label">Delivered</div>
									<div class="summary-value" id="summary-delivered">0</div>
								</div>
							</div>

							<div class="dashboard-kpis">
								<div class="kpi-card">
									<div class="kpi-icon">💰</div>
									<div class="kpi-label">Average rate per shipment</div>
									<div class="kpi-value" id="kpi-rate">R 0.00</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⚖️</div>
									<div class="kpi-label">Average charged weight</div>
									<div class="kpi-value" id="kpi-weight">0.00 kg</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⏱️</div>
									<div class="kpi-label">Average collection time</div>
									<div class="kpi-value" id="kpi-collection">0.00 days</div>
								</div>
								<div class="kpi-card">
									<div class="kpi-icon">⏱️</div>
									<div class="kpi-label">Average delivery time</div>
									<div class="kpi-value" id="kpi-delivery">0.00 days</div>
								</div>
							</div>
							<div class="dashboard-shipments">
								<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
									<h5 style="margin: 0;">Shipments <span id="shipments-count-badge" class="badge badge-secondary" style="margin-left: 10px;"></span></h5>
									<div class="pagination-controls" style="display: none;">
										<button class="btn btn-sm btn-default" id="prev-page" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.prevPage(); }">
											<i class="fa fa-chevron-left"></i> Previous
										</button>
										<span style="margin: 0 15px;" id="page-info">Page 1</span>
										<button class="btn btn-sm btn-default" id="next-page" onclick="if(window.koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) { koraflow_core.courier_guy.dashboard.nextPage(); }">
											Next <i class="fa fa-chevron-right"></i>
										</button>
									</div>
								</div>
								<div class="shipments-table-container">
									<table class="table table-bordered shipments-table">
										<thead>
											<tr>
												<th>Waybill No.</th>
												<th>Status</th>
												<th>Service</th>
												<th>Collection Address</th>
												<th>Created</th>
												<th>Delivery Address</th>
											</tr>
										</thead>
										<tbody id="shipments-tbody">
										</tbody>
									</table>
								</div>
							</div>
						</div>
						<div class="dashboard-error" style="display: none;"></div>
					`;

					// Insert at the top of the workspace content
					// The dashboard_container should be .layout-main-section based on the DOM path
					// Try to insert after any existing headers or at the very beginning
					const firstHeader = dashboard_container.querySelector('h1, h2, h3, h4, .header, [data-type="header"], .ce-block[data-type="header"]');
					if (firstHeader) {
						// Find the parent block or insert after the header's parent
						const headerParent = firstHeader.closest('.ce-block, .workspace-block') || firstHeader.parentElement;
						if (headerParent && headerParent.nextSibling) {
							headerParent.parentElement.insertBefore(api_dashboard, headerParent.nextSibling);
						} else if (headerParent) {
							headerParent.parentElement.insertBefore(api_dashboard, headerParent);
						} else {
							dashboard_container.insertBefore(api_dashboard, dashboard_container.firstChild);
						}
					} else if (dashboard_container.firstChild) {
						dashboard_container.insertBefore(api_dashboard, dashboard_container.firstChild);
					} else {
						dashboard_container.appendChild(api_dashboard);
					}


					// Dashboard rendered. Data loads when user clicks Apply.
				}

				async fetch_dashboard_data() {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');
					const error = dashboard.querySelector('.dashboard-error');

					if (!loading || !content || !error) {
						return;
					}

					try {
						loading.style.display = 'block';
						content.style.display = 'none';
						error.style.display = 'none';

						// Get date filters
						const fromDate = dashboard.querySelector('#dashboard-from-date')?.value || null;
						const toDate = dashboard.querySelector('#dashboard-to-date')?.value || null;

						// Fetch from Courier Guy API
						frappe.call({
							method: 'koraflow_core.api.courier_guy_dashboard.get_courier_guy_dashboard_data',
							args: {
								from_date: fromDate,
								to_date: toDate
							},
							callback: (r) => {
								if (r && r.message && r.message.success) {
									const data = r.message.data || {};

									// Check for API warning (network connectivity issues)
									if (data.api_warning) {
										console.warn('Courier Guy Dashboard: API Warning:', data.api_warning);
										// Show warning but still render dashboard with local data
										this.show_api_warning(data.api_warning);
									}

									// Ensure stats object exists
									if (!data.stats && data.summary) {
										data.stats = {
											total_shipments: data.summary.created || 0,
											delivered: data.summary.delivered || 0,
											in_transit: 0,
											pending: 0,
											failed: 0
										};
									}

									this.render_dashboard(data);
								} else {
									const errorMsg = r?.message?.error || r?.message || 'Failed to load dashboard data';
									this.show_error(errorMsg);
								}
							},
							error: (r) => {
								this.show_error(r?.message || r?.exc || 'Error connecting to Courier Guy API');
							}
						});

					} catch (e) {
						this.show_error(e.message || 'Unknown error occurred');
					}
				}

				applyFilters() {
					this.fetch_dashboard_data();
				}

				render_dashboard(data) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');

					if (!loading || !content) {
						return;
					}

					loading.style.display = 'none';
					content.style.display = 'block';

					// Ensure stats are visible even if 0

					// Render summary cards
					const summary = data.summary || {};
					const stats = data.stats || {};
					const summaryCreated = dashboard.querySelector('#summary-created');
					const summaryCollected = dashboard.querySelector('#summary-collected');
					const summaryDelivered = dashboard.querySelector('#summary-delivered');

					// Use stats if available, otherwise fall back to summary
					const createdValue = stats.total_shipments !== undefined ? stats.total_shipments : (summary.created || 0);
					const collectedValue = summary.collected || 0;
					const deliveredValue = stats.delivered !== undefined ? stats.delivered : (summary.delivered || 0);

					if (summaryCreated) {
						summaryCreated.textContent = createdValue;
					}
					if (summaryCollected) {
						summaryCollected.textContent = collectedValue;
					}
					if (summaryDelivered) {
						summaryDelivered.textContent = deliveredValue;
					}

					// Render KPIs
					const kpis = data.kpis || {};
					const kpiRate = dashboard.querySelector('#kpi-rate');
					const kpiWeight = dashboard.querySelector('#kpi-weight');
					const kpiCollection = dashboard.querySelector('#kpi-collection');
					const kpiDelivery = dashboard.querySelector('#kpi-delivery');

					if (kpiRate) kpiRate.textContent = `R ${(kpis.avg_rate || 0).toFixed(2)}`;
					if (kpiWeight) kpiWeight.textContent = `${(kpis.avg_weight || 0).toFixed(2)} kg`;
					if (kpiCollection) kpiCollection.textContent = `${(kpis.avg_collection_time || 0).toFixed(2)} days`;
					if (kpiDelivery) kpiDelivery.textContent = `${(kpis.avg_delivery_time || 0).toFixed(2)} days`;

					// Store all shipments and reset to page 1
					this.allShipments = data.shipments || [];
					this.currentPage = 1;

					// Render shipments table with pagination
					this.renderPaginatedShipments();

					// Update shipments count badge
					const totalCount = data.total_shipments_count || this.allShipments.length || 0;
					const countBadge = dashboard.querySelector('#shipments-count-badge');
					if (countBadge) {
						countBadge.textContent = `${totalCount}`;
						countBadge.className = 'badge badge-secondary';
					}
				}

				renderPaginatedShipments() {
					const startIdx = (this.currentPage - 1) * this.itemsPerPage;
					const endIdx = startIdx + this.itemsPerPage;
					const paginatedShipments = this.allShipments.slice(startIdx, endIdx);

					this.render_shipments_table(paginatedShipments);
					this.updatePaginationControls();
				}

				updatePaginationControls() {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) return;

					const paginationControls = dashboard.querySelector('.pagination-controls');
					const pageInfo = dashboard.querySelector('#page-info');
					const prevBtn = dashboard.querySelector('#prev-page');
					const nextBtn = dashboard.querySelector('#next-page');

					if (!paginationControls) return;

					const totalPages = Math.ceil(this.allShipments.length / this.itemsPerPage);

					// Show pagination only if there are multiple pages
					if (totalPages > 1) {
						paginationControls.style.display = 'block';
						if (pageInfo) {
							pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
						}
						if (prevBtn) {
							prevBtn.disabled = this.currentPage === 1;
						}
						if (nextBtn) {
							nextBtn.disabled = this.currentPage === totalPages;
						}
					} else {
						paginationControls.style.display = 'none';
					}
				}

				prevPage() {
					if (this.currentPage > 1) {
						this.currentPage--;
						this.renderPaginatedShipments();
					}
				}

				nextPage() {
					const totalPages = Math.ceil(this.allShipments.length / this.itemsPerPage);
					if (this.currentPage < totalPages) {
						this.currentPage++;
						this.renderPaginatedShipments();
					}
				}

				render_shipments_chart(chartData) {
					// Chart rendering removed - charts are no longer displayed
					return;
				}

				render_service_level_chart(serviceLevels) {
					// Chart rendering removed - charts are no longer displayed
					return;

				}

				render_shipments_table(shipments) {
					const tbody = document.querySelector('.courier-guy-api-dashboard #shipments-tbody') ||
						document.getElementById('shipments-tbody');
					if (!tbody) {
						console.warn('Courier Guy Dashboard: Shipments table body not found');
						return;
					}

					if (!shipments || shipments.length === 0) {
						tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No shipments found for the selected period.</td></tr>';
						return;
					}

					tbody.innerHTML = shipments.map(shipment => `
						<tr class="shipment-row" data-id="${shipment.waybill_number || shipment.name}" style="cursor: pointer;">
							<td>${shipment.waybill_number || shipment.name || '-'}</td>
							<td><span class="badge badge-${this.get_status_color(shipment.status)}">${shipment.status || '-'}</span></td>
							<td>${shipment.service || shipment.service_type || 'N/A'}</td>
							<td>${this.format_address(shipment.collection_address) || '-'}</td>
							<td>${shipment.created || shipment.date || '-'}</td>
							<td>${this.format_address(shipment.delivery_address) || '-'}</td>
						</tr>
					`).join('');

					// Add click listeners
					tbody.querySelectorAll('.shipment-row').forEach(row => {
						row.addEventListener('click', () => {
							const waybillNumber = row.getAttribute('data-id');
							const shipment = shipments.find(s => (s.waybill_number || s.name) === waybillNumber);
							if (shipment) {
								this.show_shipment_details(shipment);
							}
						});
					});
				}

				show_shipment_details(shipment) {
					console.log('Showing details for:', shipment);

					// Pull rich data from raw_data if available
					const raw = shipment.raw_data || {};
					const colAddr = raw.collection_address || {};
					const delAddr = raw.delivery_address || {};
					const colContact = raw.collection_contact || {};
					const delContact = raw.delivery_contact || {};
					const parcels = raw.parcels || [];
					const rates = raw.rates || [];
					const account = raw.account || {};

					// Format full address
					const fmtAddr = (addr) => {
						if (!addr || typeof addr !== 'object') return 'N/A';
						return [
							addr.street_address,
							addr.local_area || addr.geo_local_area,
							addr.city || addr.geo_city,
							addr.code,
							addr.zone,
							addr.country
						].filter(Boolean).join('<br>');
					};

					// Format date nicely
					const fmtDate = (dateStr) => {
						if (!dateStr) return 'N/A';
						try {
							const d = new Date(dateStr);
							return d.toLocaleDateString('en-ZA', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
						} catch (e) { return dateStr; }
					};

					const fmtDateTime = (dateStr) => {
						if (!dateStr) return 'N/A';
						try {
							const d = new Date(dateStr);
							return d.toLocaleDateString('en-ZA', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
								+ ' ' + d.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' });
						} catch (e) { return dateStr; }
					};

					// Build parcels table rows
					const parcelsHtml = parcels.length > 0 ? parcels.map((p, i) => `
						<tr>
							<td>${i + 1}</td>
							<td>${p.packaging || 'Custom parcel'}</td>
							<td>${p.parcel_description || '-'}</td>
							<td>${p.submitted_length_cm || 0} x ${p.submitted_width_cm || 0} x ${p.submitted_height_cm || 0} cm</td>
							<td>${p.submitted_weight_kg || p.actual_weight_kg || 0} kg</td>
							<td>${p.tracking_reference || '-'}</td>
							<td><span class="badge badge-${this.get_status_color(p.status || '')}">${this.format_status_text(p.status)}</span></td>
						</tr>
					`).join('') : '<tr><td colspan="7" class="text-center text-muted">No parcel details</td></tr>';

					// Build rates breakdown
					const baseRates = rates.filter(r => r.type === 'base' || r.type === 'rate_formula');
					const optInRates = raw.opt_in_rates || [];
					let rateBreakdownHtml = '';
					if (baseRates.length > 0) {
						rateBreakdownHtml = baseRates.map(r =>
							`<li>${r.name || r.type}: R ${parseFloat(r.value || 0).toFixed(2)} (VAT: R ${parseFloat(r.vat || 0).toFixed(2)})</li>`
						).join('');
					}
					if (optInRates.length > 0) {
						rateBreakdownHtml += optInRates.map(r =>
							`<li>${r.name || 'Add-on'}: R ${parseFloat(r.value || 0).toFixed(2)}</li>`
						).join('');
					}

					const statusColor = this.get_status_color(shipment.status);

					const d = new frappe.ui.Dialog({
						title: `Shipment: ${shipment.waybill_number || shipment.name}`,
						size: 'extra-large',
						fields: [
							{
								fieldname: 'shipment_details_html',
								fieldtype: 'HTML',
								options: `
								<div style="font-size: 13px;">
									<!-- Shipment Details -->
									<div style="background: var(--bg-light-gray, #f5f5f5); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
										<h5 style="margin-top: 0;">Shipment Details</h5>
										<div style="display: flex; gap: 24px; flex-wrap: wrap;">
											<div><strong>Service level:</strong> ${raw.service_level_name || shipment.service_type || 'N/A'} (${raw.service_level_code || ''})</div>
											<div><strong>Status:</strong> <span class="badge badge-${statusColor}">${shipment.status}</span></div>
										</div>
										<div style="margin-top: 8px; color: var(--text-muted);">
											Created: ${fmtDateTime(raw.time_created)} by ${raw.created_by || 'N/A'}
										</div>
									</div>

									<!-- Collection & Delivery side by side -->
									<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
										<!-- Collection -->
										<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px;">
											<h5 style="margin-top: 0;">Collection</h5>
											<p><strong>Expected collection:</strong> ${fmtDate(raw.estimated_collection)}</p>
											${raw.collected_date ? `<p><strong>Collected:</strong> ${fmtDate(raw.collected_date)}</p>` : ''}
											<hr>
											<h6>Address and instructions</h6>
											<p>${fmtAddr(colAddr)}</p>
											${raw.special_instructions_collection ? `<p style="color: var(--text-muted); font-style: italic;">${raw.special_instructions_collection}</p>` : ''}
											<hr>
											<h6>Contact details</h6>
											<p>
												<strong>Name:</strong> ${colContact.name || 'N/A'}<br>
												<strong>Email:</strong> ${colContact.email || '-'}<br>
												<strong>Phone:</strong> ${colContact.mobile_number || '-'}
											</p>
										</div>
										<!-- Delivery -->
										<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px;">
											<h5 style="margin-top: 0;">Delivery</h5>
											<p><strong>Expected delivery:</strong> ${fmtDate(raw.estimated_delivery_from)}${raw.estimated_delivery_to ? ' - ' + fmtDate(raw.estimated_delivery_to) : ''}</p>
											${raw.delivered_date ? `<p><strong>Delivered:</strong> ${fmtDate(raw.delivered_date)}</p>` : ''}
											<hr>
											<h6>Address and instructions</h6>
											<p>${fmtAddr(delAddr)}</p>
											${raw.special_instructions_delivery ? `<p style="color: var(--text-muted); font-style: italic;">${raw.special_instructions_delivery}</p>` : ''}
											<hr>
											<h6>Contact details</h6>
											<p>
												<strong>Name:</strong> ${delContact.name || 'N/A'}<br>
												<strong>Email:</strong> ${delContact.email || '-'}<br>
												<strong>Phone:</strong> ${delContact.mobile_number || '-'}
											</p>
										</div>
									</div>

									<!-- Parcel Details -->
									<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
										<h5 style="margin-top: 0;">Parcel Details</h5>
										<div style="overflow-x: auto;">
											<table class="table table-bordered table-sm" style="margin-bottom: 0;">
												<thead style="background: #fef3cd;">
													<tr>
														<th>#</th>
														<th>Package Type</th>
														<th>Parcel Category</th>
														<th>Dimensions</th>
														<th>Weight</th>
														<th>Tracking Ref.</th>
														<th>Status</th>
													</tr>
												</thead>
												<tbody>${parcelsHtml}</tbody>
											</table>
										</div>
									</div>

									<!-- Service Type -->
									<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
										<h5 style="margin-top: 0;">Service Type</h5>
										<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
											<div><strong>Service level:</strong> ${raw.service_level_name || 'N/A'} (${raw.service_level_code || ''})</div>
											<div><strong>Charged weight:</strong> ${raw.charged_weight || 0} kg</div>
											<div><strong>Expected collection:</strong> ${fmtDate(raw.estimated_collection)}</div>
											<div><strong>Actual weight:</strong> ${raw.actual_weight || 0} kg</div>
											<div><strong>Expected delivery:</strong> ${fmtDate(raw.estimated_delivery_from)}${raw.estimated_delivery_to ? ' - ' + fmtDate(raw.estimated_delivery_to) : ''}</div>
											<div><strong>Volumetric weight:</strong> ${raw.volumetric_weight || 0} kg</div>
										</div>
										<div style="margin-top: 12px;">
											<strong>Rate:</strong> R ${parseFloat(raw.rate || 0).toFixed(2)}
											${rateBreakdownHtml ? `<ul style="margin-top: 4px;">${rateBreakdownHtml}</ul>` : ''}
										</div>
									</div>

									<!-- Billing -->
									${account.name ? `
									<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
										<h5 style="margin-top: 0;">Billing</h5>
										<p>
											<strong>${account.name || 'N/A'}</strong><br>
											${account.billing_contact ? (account.billing_contact.email || '') : ''}<br>
											${account.billing_contact ? (account.billing_contact.mobile_number || '') : ''}
										</p>
									</div>` : ''}

									<!-- Latest Tracking -->
									${raw.latest_tracking_message ? `
									<div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; padding: 16px;">
										<h5 style="margin-top: 0;">Latest Tracking</h5>
										<p>${raw.latest_tracking_message}</p>
										<p class="text-muted small">${fmtDateTime(raw.latest_tracking_event_time)}</p>
									</div>` : ''}
								</div>`
							}
						]
					});

					// Add Track button
					d.set_primary_action('Track on Courier Guy', () => {
						window.open(`https://portal.thecourierguy.co.za/shipments`, '_blank');
					});

					d.show();
				}

				format_status_text(status) {
					if (!status) return 'N/A';
					return status.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
				}

				format_address(address) {
					if (!address) return '';
					// If address is a string, return it as-is
					if (typeof address === 'string') {
						// Truncate long addresses
						return address.length > 50 ? address.substring(0, 47) + '...' : address;
					}
					// If address is an object, format it
					if (typeof address === 'object') {
						const parts = [];
						if (address.address_line1) parts.push(address.address_line1);
						if (address.suburb) parts.push(address.suburb);
						if (address.city) parts.push(address.city);
						return parts.join(', ') || '';
					}
					return '';
				}

				get_status_color(status) {
					const s = status ? status.toLowerCase() : '';
					if (s.includes('delivered')) return 'success';
					if (s.includes('transit') || s.includes('assigned') || s.includes('request') || s.includes('out for delivery')) return 'primary';
					if (s.includes('pending') || s.includes('draft') || s.includes('created')) return 'warning';
					if (s.includes('fail') || s.includes('cancel')) return 'danger';
					return 'secondary';
				}

				show_api_warning(message) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) return;

					const warningDiv = dashboard.querySelector('.dashboard-api-warning');
					const warningMsg = dashboard.querySelector('.dashboard-api-warning .warning-message');

					if (warningDiv && warningMsg) {
						warningMsg.textContent = message;
						warningDiv.style.display = 'block';
					}
				}

				show_error(message) {
					const dashboard = document.querySelector('.courier-guy-api-dashboard');
					if (!dashboard) {
						return;
					}

					const loading = dashboard.querySelector('.dashboard-loading');
					const content = dashboard.querySelector('.dashboard-content');
					const error = dashboard.querySelector('.dashboard-error');

					if (!loading || !content || !error) {
						return;
					}

					loading.style.display = 'none';
					content.style.display = 'none';
					error.style.display = 'block';
					error.innerHTML = `
						<div class="alert alert-danger">
							<strong>Error:</strong> ${message}
							<br><small>Make sure Courier Guy Settings are configured correctly.</small>
						</div>
					`;
				}

				refresh() {
					this.fetch_dashboard_data();
				}

				// Cleanup charts on destroy
				destroy() {
					if (this.shipmentsChart) {
						this.shipmentsChart.destroy();
					}
					if (this.serviceLevelChart) {
						this.serviceLevelChart.destroy();
					}
				}
			};
		}

		// Initialize dashboard instance
		if (!koraflow_core.courier_guy.dashboard) {
			koraflow_core.courier_guy.dashboard = new koraflow_core.courier_guy.Dashboard();
		}

		// Also try direct injection on page load
		$(document).ready(function () {
			setTimeout(function () {
				try {
					if (typeof frappe !== 'undefined' && frappe.get_route && typeof frappe.get_route === 'function') {
						let route;
						try {
							route = frappe.get_route();
						} catch (e) {
							return; // get_route failed, exit early
						}
						if (route && Array.isArray(route) && route.length >= 2) {
							const first = route[0];
							const second = String(route[1] || '').toLowerCase();
							// Check for both "Courier Guy" (space) and "courier-guy" (hyphen) formats
							if (first === 'workspace' && (
								second === 'courier guy' ||
								second === 'courier-guy' ||
								second.includes('courier') && second.includes('guy')
							)) {
								if (!document.querySelector('.courier-guy-api-dashboard')) {
									if (koraflow_core && koraflow_core.courier_guy && koraflow_core.courier_guy.dashboard) {
										koraflow_core.courier_guy.dashboard.load_dashboard_data();
									}
								}
							}
						}
					}
				} catch (e) {
				}
			}, 3000);
		});
	}

	// Start initialization - wait for Frappe to be fully loaded
	const waitForFrappe = () => {
		if (typeof frappe !== 'undefined' && typeof frappe.provide === 'function') {
			initDashboard();
		} else {
			setTimeout(waitForFrappe, 100);
		}
	};

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', waitForFrappe);
	} else {
		// If DOM already loaded, wait for Frappe
		waitForFrappe();
	}


})();
