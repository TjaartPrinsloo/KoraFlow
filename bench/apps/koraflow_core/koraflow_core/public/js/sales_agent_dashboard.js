// Copyright (c) 2024, KoraFlow Team and Contributors
// License: MIT. See LICENSE
// Updated: 2025-01-07 - Fixed frappe.ready error

frappe.provide("koraflow_core.sales_agent");

koraflow_core.sales_agent.Dashboard = class {
	constructor(container) {
		this.container = container || this.find_container();
		this.init();
	}

	find_container() {
		// Try to find the dashboard container
		let container = document.querySelector('.sales-agent-dashboard-container');
		if (!container) {
			// Try workspace content
			container = document.querySelector('.workspace-content');
		}
		if (!container) {
			// Try page content area
			container = document.querySelector('.page-content');
		}
		if (!container) {
			// Create a container
			container = document.createElement('div');
			container.className = 'sales-agent-dashboard-container';
			const page_content = document.querySelector('.layout-main-section') || document.body;
			page_content.appendChild(container);
		}
		return container;
	}

	init() {
		// Wait for page to fully load
		setTimeout(() => {
			this.load_dashboard_data();
			this.setup_refresh();
		}, 500);
	}

	load_dashboard_data() {
		frappe.call({
			method: "koraflow_core.koraflow_core.api.sales_agent_dashboard.get_dashboard_data",
			callback: (r) => {
				if (r.message) {
					this.render_dashboard(r.message);
				}
			}
		});
	}

	render_dashboard(data) {
		this.render_commission_kpis(data.commission_summary);
		this.render_referrals_table(data.referrals);
		this.render_messages(data.messages);
		this.render_status_chart(data.status_distribution);
	}

	render_commission_kpis(summary) {
		// Find or create KPI container
		let kpi_container = document.querySelector('.commission-kpis');
		if (!kpi_container) {
			// Create in dashboard container
			if (this.container) {
				kpi_container = document.createElement('div');
				kpi_container.className = 'commission-kpis row';
				this.container.insertBefore(kpi_container, this.container.firstChild);
			} else {
				// Fallback: try to find container
				const container = this.find_container();
				if (container) {
					kpi_container = document.createElement('div');
					kpi_container.className = 'commission-kpis row';
					container.insertBefore(kpi_container, container.firstChild);
				}
			}
		}

		if (!kpi_container) return;

		const kpis = [
			{
				label: __('Total Commission Earned'),
				value: this.format_currency(summary.total_earned || 0),
				color: 'green'
			},
			{
				label: __('Pending Commission'),
				value: this.format_currency(summary.pending || 0),
				color: 'orange'
			},
			{
				label: __('Paid Commission'),
				value: this.format_currency(summary.paid || 0),
				color: 'blue'
			},
			{
				label: __('This Month'),
				value: this.format_currency(summary.this_month || 0),
				subtitle: `${summary.month_change >= 0 ? '+' : ''}${summary.month_change}% vs last month`,
				color: summary.month_change >= 0 ? 'green' : 'red'
			}
		];

		kpi_container.innerHTML = kpis.map(kpi => `
			<div class="col-md-3 col-sm-6">
				<div class="kpi-card">
					<div class="kpi-value ${kpi.color}">${kpi.value}</div>
					<div class="kpi-label">${kpi.label}</div>
					${kpi.subtitle ? `<div class="kpi-subtitle">${kpi.subtitle}</div>` : ''}
				</div>
			</div>
		`).join('');
	}

	render_referrals_table(referrals) {
		// Create referrals section if it doesn't exist
		let table_container = document.querySelector('.referrals-table-container');
		if (!table_container) {
			const container = this.container || this.find_container();
			if (container) {
				const section = document.createElement('div');
				section.className = 'referrals-section';
				section.innerHTML = `
					<h4>${__('My Referrals')}</h4>
					<div class="referrals-table-container"></div>
				`;
				container.appendChild(section);
				table_container = section.querySelector('.referrals-table-container');
			}
		}

		if (!table_container) return;

		if (!referrals || referrals.length === 0) {
			table_container.innerHTML = '<div class="text-muted">No referrals found</div>';
			return;
		}

		const table_html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>${__('Patient Name')}</th>
						<th>${__('Referral Date')}</th>
						<th>${__('Current Status')}</th>
						<th>${__('Last Update')}</th>
						<th>${__('Actions')}</th>
					</tr>
				</thead>
				<tbody>
					${referrals.map(ref => `
						<tr>
							<td>${ref.patient_name_display || `${ref.patient_first_name || ''} ${ref.patient_last_name || ''}`.trim()}</td>
							<td>${frappe.datetime.str_to_user(ref.referral_date)}</td>
							<td><span class="badge badge-secondary">${ref.current_journey_status || ''}</span></td>
							<td>${ref.last_status_update ? frappe.datetime.str_to_user(ref.last_status_update) : ''}</td>
							<td>
								<button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form', 'Patient Referral', '${ref.name}')">
									${__('View')}
								</button>
							</td>
						</tr>
					`).join('')}
				</tbody>
			</table>
		`;

		table_container.innerHTML = table_html;
	}

	render_messages(messages) {
		let messages_container = document.querySelector('.messages-container');
		if (!messages_container) {
			const container = this.container || this.find_container();
			if (container) {
				const section = document.createElement('div');
				section.className = 'messages-section';
				section.innerHTML = `
					<h4>${__('Recent Messages')}</h4>
					<div class="messages-container"></div>
				`;
				container.appendChild(section);
				messages_container = section.querySelector('.messages-container');
			}
		}

		if (!messages_container) return;

		if (!messages || messages.length === 0) {
			messages_container.innerHTML = '<div class="text-muted">No messages</div>';
			return;
		}

		const messages_html = messages.map(msg => `
			<div class="message-item ${msg.status === 'Unread' ? 'unread' : ''}">
				<div class="message-header">
					<strong>${msg.subject}</strong>
					<span class="badge badge-${msg.status === 'Unread' ? 'danger' : 'secondary'}">${msg.status}</span>
				</div>
				<div class="message-meta">
					${msg.from_user === frappe.session.user ? __('To') : __('From')}: ${msg.from_user === frappe.session.user ? msg.to_user : msg.from_user}
					<span class="text-muted"> - ${frappe.datetime.str_to_user(msg.created_at)}</span>
				</div>
			</div>
		`).join('');

		messages_container.innerHTML = messages_html;
	}

	render_status_chart(distribution) {
		let chart_container = document.querySelector('.status-chart-container');
		if (!chart_container) {
			const container = this.container || this.find_container();
			if (container) {
				const section = document.createElement('div');
				section.className = 'status-chart-section';
				section.innerHTML = `
					<h4>${__('Status Distribution')}</h4>
					<div class="status-chart-container"></div>
				`;
				container.appendChild(section);
				chart_container = section.querySelector('.status-chart-container');
			}
		}

		if (!chart_container) return;

		const total = Object.values(distribution).reduce((a, b) => a + b, 0);
		if (total === 0) {
			chart_container.innerHTML = '<div class="text-muted">No data available</div>';
			return;
		}

		const chart_html = Object.entries(distribution).map(([status, count]) => {
			const percentage = (count / total) * 100;
			return `
				<div class="status-bar-item">
					<div class="status-label">${status}</div>
					<div class="status-bar">
						<div class="status-bar-fill" style="width: ${percentage}%"></div>
					</div>
					<div class="status-count">${count}</div>
				</div>
			`;
		}).join('');

		chart_container.innerHTML = chart_html;
	}

	format_currency(amount) {
		return format_currency(amount, frappe.defaults.get_default("currency"), 2);
	}

	setup_refresh() {
		// Auto-refresh every 5 minutes
		setInterval(() => {
			this.load_dashboard_data();
		}, 5 * 60 * 1000);
	}
};

// Initialize dashboard when on Sales Agent Dashboard workspace
// Note: This is handled by the custom page's on_page_load function
// The Dashboard class is available for use in custom blocks or other contexts
// Removed frappe.ready check as it's not available in this context
// Version: 2025-01-07-v2 - Fixed frappe.ready error
