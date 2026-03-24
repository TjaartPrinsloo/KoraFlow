
// Wrapper for Frappe API calls (POST with session cookie + CSRF)
async function apiCall(method, args) {
    const csrfToken = window.csrf_token || '';
    const response = await fetch('/api/method/' + method, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': csrfToken
        },
        body: JSON.stringify(args || {})
    });
    const data = await response.json();
    if (data.exc) {
        throw new Error(data._server_messages || data.exc || 'Server error');
    }
    return data.message;
}

document.addEventListener('DOMContentLoaded', function () {
    // Initialize if dashboard elements exist
    if (document.getElementById('stat-referrals')) {
        initDashboard();
    }
});

function initDashboard() {
    loadDashboardData();
    setupEventListeners();
}

async function loadDashboardData() {
    try {
        // Use server-rendered data on first load, API for refreshes
        if (window._dashboardData && Object.keys(window._dashboardData).length > 0) {
            const data = window._dashboardData;
            window._dashboardData = null; // Only use once
            updateDashboardUI(data);
        } else {
            const data = await apiCall('koraflow_core.api.sales_agent_dashboard.get_dashboard_data');
            if (data) updateDashboardUI(data);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateDashboardUI(data) {
    // Update KPI stats
    if (data.referrals) {
        const refCount = document.getElementById('stat-referrals');
        if (refCount) refCount.innerText = data.referrals.length;
    }

    if (data.commission_summary) {
        const summary = data.commission_summary;

        const totalEarned = document.getElementById('total-earned');
        // Format with ZAR currency style but replace name for cleaner UI if needed
        if (totalEarned) totalEarned.innerText = formatCurrency(summary.total_earned || 0);

        const availBalance = document.getElementById('available-balance');
        // Available = accrued minus pending payout requests (use ?? to handle 0 correctly)
        const balanceValue = summary.available ?? summary.pending ?? 0;
        if (availBalance) availBalance.innerText = formatCurrency(balanceValue);

        // Update modal balance as well
        const modalBalance = document.getElementById('modal-balance');
        if (modalBalance) modalBalance.innerText = formatCurrency(balanceValue);

        // Update slider max
        const slider = document.getElementById('payout-slider');
        const amountInput = document.getElementById('payout-amount');
        const sliderMaxLabel = document.getElementById('slider-max');

        if (slider && amountInput) {
            slider.max = balanceValue;
            if (sliderMaxLabel) sliderMaxLabel.innerText = formatCurrency(balanceValue);

            slider.value = 0;
            amountInput.value = 0;
        }

        // Handle Bank Details Configured State
        const methodContainer = document.getElementById('payment-method-container');
        const noBillingInfo = document.getElementById('no-billing-info');
        const requestBtn = document.getElementById('request-payout-btn');
        const confirmBtn = document.querySelector('#payout-modal button[onclick="submitPayoutRequest()"]');
        const methodSelect = document.getElementById('payment-method');

        if (data.agent) {
            // UPDATE: Use the correct Sales Agent DocName for submissions
            if (data.agent.name) {
                window.sales_agent_doc_name = data.agent.name;
            }

            if (data.agent.bank_details_configured) {
                if (methodContainer) methodContainer.classList.remove('hidden');
                if (noBillingInfo) noBillingInfo.classList.add('hidden');
                if (requestBtn) requestBtn.disabled = false;
                if (confirmBtn) confirmBtn.disabled = false;

                // Populate method select if empty
                if (methodSelect && methodSelect.options.length <= 1) {
                    methodSelect.innerHTML = `<option value="bank_transfer" selected>Bank Transfer (EFT)</option>`;
                }
            } else {
                if (methodContainer) methodContainer.classList.add('hidden');
                if (noBillingInfo) noBillingInfo.classList.remove('hidden');
                // Optionally disable request button, but better to let them click and see the modal with warning
                if (confirmBtn) {
                    confirmBtn.disabled = false; // Allow click but maybe show error? Actually previously we disabled. Let's keep enabled but show warning in modal.
                    // confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');
                    confirmBtn.innerText = "Setup Banking First";
                }
            }
        }
    }

    // Render Referrals Table
    const tbody = document.getElementById('referrals-tbody');
    if (tbody && data.referrals && data.referrals.length > 0) {
        tbody.innerHTML = data.referrals.map(ref => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border-b border-slate-100 dark:border-slate-800 last:border-0">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-medium">
                    ${formatDate(ref.referral_date)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-charcoal font-bold text-xs mr-3 shadow-sm">
                            ${getInitials(ref.patient_name_display || 'Unknown')}
                        </div>
                        <div class="text-sm font-bold text-charcoal dark:text-white">${ref.patient_name_display || 'Unknown'}</div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-0.5 inline-flex text-xs leading-5 font-bold rounded uppercase tracking-wider bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        ${ref.current_journey_status || 'New'}
                    </span>
                </td>
            </tr>
        `).join('');
    } else if (tbody) {
        tbody.innerHTML = `<tr><td colspan="3" class="px-6 py-8 text-center text-slate-400 font-medium bg-slate-50/50">No referrals found yet.</td></tr>`;
    }

    // Render Commission History
    const historyContainer = document.getElementById('commission-history');
    if (historyContainer && data.commission_history && data.commission_history.length > 0) {
        historyContainer.innerHTML = data.commission_history.map(comm => `
            <div class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border border-transparent hover:border-slate-100 dark:hover:border-slate-700">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-green-50 flex items-center justify-center text-green-600">
                        <span class="material-symbols-outlined text-sm">payments</span>
                    </div>
                    <div>
                        <p class="text-sm font-bold text-charcoal dark:text-white">${comm.invoice_reference}</p>
                        <p class="text-xs text-slate-400">${formatDate(comm.creation)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-sm font-bold text-primary filter brightness-90">${formatCurrency(comm.accrued_amount)}</p>
                    <span class="text-[10px] font-bold uppercase tracking-wider ${
                        comm.display_status === 'Paid Out' ? 'text-green-600' :
                        comm.display_status === 'In Wallet' ? 'text-primary' : 'text-slate-400'
                    }">${comm.display_status || comm.status}</span>
                </div>
            </div>
        `).join('');
    } else if (historyContainer) {
        historyContainer.innerHTML = `<div class="text-center text-slate-400 font-medium py-8">No commission history yet.</div>`;
    }

    // Update KPI Stats
    if (data.kpi_stats) {
        setText('stat-referrals', data.kpi_stats.total_referrals);
        setText('stat-conversion', data.kpi_stats.conversion_rate + '%');
        setText('stat-patients', data.kpi_stats.total_patients);
        setText('stat-ticket', formatCurrency(data.kpi_stats.avg_ticket));
    }

    // Hide Compliance Status Card
    const complianceCard = document.getElementById('compliance-status-card');
    if (complianceCard) {
        complianceCard.classList.add('hidden');
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value;
}

function getInitials(name) {
    if (!name) return '??';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount).replace('ZAR', 'R');
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-ZA', { day: '2-digit', month: 'short', year: 'numeric' });
}

function setupEventListeners() {
    // Payout Request Button
    const btn = document.getElementById('request-payout-btn');
    if (btn) {
        btn.addEventListener('click', openPayoutModal);
    }

    // Close buttons handled by onclick in HTML, but we can add escape key listener
    document.addEventListener('keydown', function (event) {
        if (event.key === "Escape") {
            closePayoutModal();
            closeSuccessModal();
        }
    });

    // Make functions globally available for HTML onclick attributes
    window.openPayoutModal = openPayoutModal;
    window.closePayoutModal = closePayoutModal;
    window.submitPayoutRequest = submitPayoutRequest;
    window.closeSuccessModal = closeSuccessModal;

    // Slider Synchronization with Logging (Event Delegation)
    console.log('Attaching delegated slider events');

    // Sync Input -> Slider (Delegated)
    document.addEventListener('input', function (e) {
        if (e.target && e.target.id === 'payout-slider') {
            const amountInput = document.getElementById('payout-amount');
            if (amountInput) {
                console.log('Slider input (delegated):', e.target.value);
                amountInput.value = e.target.value;
            }
        }

        // Sync Slider -> Input (Delegated)
        if (e.target && e.target.id === 'payout-amount') {
            const slider = document.getElementById('payout-slider');
            if (slider) {
                let val = parseFloat(e.target.value);
                if (val > slider.max) val = slider.max;
                if (val < 0) val = 0;
                slider.value = val;
            }
        }
    });
}

function openPayoutModal() {
    const modal = document.getElementById('payout-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closePayoutModal() {
    const modal = document.getElementById('payout-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function closeSuccessModal() {
    const modal = document.getElementById('success-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

async function submitPayoutRequest() {
    const amountEl = document.getElementById('payout-amount');
    const notesEl = document.getElementById('payout-notes');

    if (!amountEl) return;

    const amount = parseFloat(amountEl.value);
    const notes = notesEl ? notesEl.value : '';

    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
        return;
    }

    // Disable button to prevent double-clicks
    const submitBtn = document.querySelector('#payout-modal button[onclick="submitPayoutRequest()"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Processing...';
    }

    try {
        const result = await apiCall('koraflow_core.api.agent_portal.request_payout', { amount: amount });

        closePayoutModal();

        // Show success modal
        const successModal = document.getElementById('success-modal');
        if (successModal) successModal.classList.add('active');

        // Update success modal details
        const reqId = document.getElementById('request-id');
        const reqAmt = document.getElementById('request-amount');

        if (reqId && result) reqId.innerText = result.name || '---';
        if (reqAmt) reqAmt.innerText = formatCurrency(amount);

        // Refresh dashboard data
        loadDashboardData();
    } catch (error) {
        console.error('Error submitting payout:', error);
        alert(error.message || 'An error occurred. Please check your connection.');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="material-symbols-outlined text-sm">send</span> Submit Request';
        }
    }
}
// ... existing code ...

function openNewReferralModal() {
    const modal = document.getElementById('new-referral-modal');
    if (modal) {
        modal.classList.add('active');
        // Focus first input
        setTimeout(() => document.getElementById('ref-first-name')?.focus(), 100);
    }
}

function closeNewReferralModal() {
    const modal = document.getElementById('new-referral-modal');
    if (modal) {
        modal.classList.remove('active');
        // Clear inputs
        document.getElementById('ref-first-name').value = '';
        document.getElementById('ref-last-name').value = '';
        document.getElementById('ref-email').value = '';
        document.getElementById('ref-mobile').value = '';
    }
}

async function submitNewReferral() {
    const btn = document.querySelector('#new-referral-modal button[onclick="submitNewReferral()"]');
    const originalText = btn.innerHTML;

    // Validate inputs
    const firstName = document.getElementById('ref-first-name').value;
    const lastName = document.getElementById('ref-last-name').value;
    const email = document.getElementById('ref-email').value;
    const mobile = document.getElementById('ref-mobile').value;

    if (!firstName || !lastName || !email || !mobile) {
        alert('Please fill in all fields');
        return;
    }

    try {
        btn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Creating...';
        btn.disabled = true;

        await apiCall('koraflow_core.api.sales_agent_dashboard.create_referral', {
            first_name: firstName, last_name: lastName, email: email, mobile_no: mobile
        });

        closeNewReferralModal();
        const successModal = document.getElementById('success-modal');
        if (successModal) {
            successModal.classList.add('active');
            document.querySelector('#success-modal h2').innerText = 'Referral Created!';
            document.querySelector('#success-modal p').innerText = `Successfully created referral for ${firstName} ${lastName}.`;
            const detailsBox = document.querySelector('#success-modal .bg-slate-50');
            if (detailsBox) detailsBox.classList.add('hidden');
        }
        loadDashboardData();
    } catch (error) {
        console.error('Error creating referral:', error);
        alert('Connection error. Please try again.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Ensure global access
window.openNewReferralModal = openNewReferralModal;
window.closeNewReferralModal = closeNewReferralModal;
window.submitNewReferral = submitNewReferral;
window.openSupportModal = openSupportModal;
window.closeSupportModal = closeSupportModal;
window.submitSupportTicket = submitSupportTicket;

// ========== CRM TAB FUNCTIONS ==========

window.switchTab = switchTab;
window.onAgentFilterChange = onAgentFilterChange;
window.openReminderModal = openReminderModal;
window.closeReminderModal = closeReminderModal;
window.confirmSendReminder = confirmSendReminder;
window.openActivityModal = openActivityModal;
window.closeActivityModal = closeActivityModal;
window.selectActivityType = selectActivityType;
window.submitActivity = submitActivity;
window.openTimelineModal = openTimelineModal;
window.closeTimelineModal = closeTimelineModal;
window.openActivityFromTimeline = openActivityFromTimeline;

let crmDataLoaded = false;

function switchTab(tabName) {
    const dashboardTab = document.getElementById('tab-dashboard');
    const crmTab = document.getElementById('tab-crm');
    const navDashboard = document.getElementById('nav-dashboard');
    const navCrm = document.getElementById('nav-crm');

    if (tabName === 'crm') {
        if (dashboardTab) dashboardTab.classList.add('hidden');
        if (crmTab) crmTab.classList.remove('hidden');
        if (navDashboard) {
            navDashboard.classList.remove('active-nav');
            navDashboard.classList.add('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
        }
        if (navCrm) {
            navCrm.classList.add('active-nav');
            navCrm.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
        }
        if (!crmDataLoaded) {
            loadCRMData();
            loadFollowups();
        }
    } else {
        if (dashboardTab) dashboardTab.classList.remove('hidden');
        if (crmTab) crmTab.classList.add('hidden');
        if (navDashboard) {
            navDashboard.classList.add('active-nav');
            navDashboard.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
        }
        if (navCrm) {
            navCrm.classList.remove('active-nav');
            navCrm.classList.add('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
        }
    }
}

async function loadCRMData(agentFilter) {
    try {
        if (!agentFilter && window._crmData && Object.keys(window._crmData).length > 0) {
            const data = window._crmData;
            window._crmData = null;
            updateCRMUI(data);
            crmDataLoaded = true;
        } else {
            const args = agentFilter ? { agent_filter: agentFilter } : {};
            const data = await apiCall('koraflow_core.api.sales_agent_dashboard.get_crm_data', args);
            if (data) {
                updateCRMUI(data);
                crmDataLoaded = true;
            }
        }
    } catch (error) {
        console.error('Error loading CRM data:', error);
    }
}

function updateCRMUI(data) {
    console.log('updateCRMUI called with data:', JSON.stringify(data).substring(0, 500));

    if (!data || typeof data === 'string') {
        console.warn('CRM data is not an object:', data);
        return;
    }

    // Update CRM Stats
    setText('crm-stat-quotes-count', data.crm_stats?.outstanding_quotes_count || 0);
    setText('crm-stat-quotes-value', formatCurrency(data.crm_stats?.outstanding_quotes_value || 0));
    setText('crm-stat-invoices-count', data.crm_stats?.overdue_invoices_count || 0);
    setText('crm-stat-invoices-value', formatCurrency(data.crm_stats?.overdue_invoices_value || 0));
    setText('crm-stat-reminders', data.crm_stats?.reminders_sent_this_month || 0);

    // Show agent filter if agents list is present (System Manager)
    if (data.agents_list && data.agents_list.length > 0) {
        const filterDiv = document.getElementById('crm-agent-filter');
        const selectEl = document.getElementById('crm-agent-select');
        if (filterDiv) filterDiv.classList.remove('hidden');
        if (selectEl && selectEl.options.length <= 1) {
            data.agents_list.forEach(agent => {
                const opt = document.createElement('option');
                opt.value = agent.value;
                opt.textContent = agent.label;
                selectEl.appendChild(opt);
            });
        }
    }

    // Render Outstanding Quotes
    const quotesTbody = document.getElementById('crm-quotes-tbody');
    console.log('quotesTbody element:', quotesTbody, 'quotes data:', data.outstanding_quotes);
    if (quotesTbody) {
        if (data.outstanding_quotes && data.outstanding_quotes.length > 0) {
            quotesTbody.innerHTML = data.outstanding_quotes.map(q => `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <div class="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-xs mr-3">
                                ${getInitials(q.masked_name)}
                            </div>
                            <span class="text-sm font-bold text-charcoal dark:text-white">${q.masked_name}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider bg-amber-100 text-amber-800">${q.status}</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-charcoal dark:text-white">${formatCurrency(q.amount)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${formatDate(q.date)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${q.days_outstanding > 7 ? 'text-red-600' : 'text-slate-500'}">${q.days_outstanding}d</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${q.patient_referral ? `
                            <div class="flex items-center gap-1.5">
                                <button onclick="openReminderModal('${q.patient_referral}', 'quote_pending', '${q.masked_name}')"
                                    ${!q.can_remind ? 'disabled' : ''}
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1
                                        ${q.can_remind
                                            ? 'bg-primary/10 text-charcoal hover:bg-primary/20'
                                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'}"
                                    ${!q.can_remind ? 'title="Reminder sent recently"' : ''}>
                                    <span class="material-symbols-outlined text-sm">send</span>
                                </button>
                                <button onclick="openActivityModal('${q.patient_referral}', '${q.masked_name}')"
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all flex items-center gap-1"
                                    title="Log Activity">
                                    <span class="material-symbols-outlined text-sm">edit_note</span>
                                </button>
                                <button onclick="openTimelineModal('${q.patient_referral}')"
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all flex items-center gap-1"
                                    title="View Timeline">
                                    <span class="material-symbols-outlined text-sm">timeline</span>
                                </button>
                            </div>
                        ` : '<span class="text-xs text-slate-400">-</span>'}
                    </td>
                </tr>
            `).join('');
        } else {
            quotesTbody.innerHTML = `<tr><td colspan="6" class="px-6 py-8 text-center text-slate-400 font-medium bg-slate-50/50">No outstanding quotes - great work!</td></tr>`;
        }
    }

    // Render Outstanding Invoices
    const invoicesTbody = document.getElementById('crm-invoices-tbody');
    if (invoicesTbody) {
        if (data.outstanding_invoices && data.outstanding_invoices.length > 0) {
            invoicesTbody.innerHTML = data.outstanding_invoices.map(inv => `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors ${inv.status === 'Overdue' ? 'bg-red-50/50 dark:bg-red-900/10' : ''}">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <div class="h-8 w-8 rounded-full ${inv.status === 'Overdue' ? 'bg-red-100' : 'bg-slate-100'} flex items-center justify-center ${inv.status === 'Overdue' ? 'text-red-700' : 'text-slate-600'} font-bold text-xs mr-3">
                                ${getInitials(inv.masked_name)}
                            </div>
                            <span class="text-sm font-bold text-charcoal dark:text-white">${inv.masked_name}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider
                            ${inv.status === 'Overdue' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}">${inv.status}</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-charcoal dark:text-white">${formatCurrency(inv.amount)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">${formatDate(inv.due_date)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${inv.days_overdue > 0 ? 'text-red-600 font-bold' : 'text-slate-500'}">${inv.days_overdue > 0 ? inv.days_overdue + 'd' : 'Not yet'}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${inv.patient_referral ? `
                            <div class="flex items-center gap-1.5">
                                <button onclick="openReminderModal('${inv.patient_referral}', 'invoice_overdue', '${inv.masked_name}')"
                                    ${!inv.can_remind ? 'disabled' : ''}
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1
                                        ${inv.can_remind
                                            ? 'bg-red-50 text-red-700 hover:bg-red-100'
                                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'}"
                                    ${!inv.can_remind ? 'title="Reminder sent recently"' : ''}>
                                    <span class="material-symbols-outlined text-sm">send</span>
                                </button>
                                <button onclick="openActivityModal('${inv.patient_referral}', '${inv.masked_name}')"
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all flex items-center gap-1"
                                    title="Log Activity">
                                    <span class="material-symbols-outlined text-sm">edit_note</span>
                                </button>
                                <button onclick="openTimelineModal('${inv.patient_referral}')"
                                    class="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all flex items-center gap-1"
                                    title="View Timeline">
                                    <span class="material-symbols-outlined text-sm">timeline</span>
                                </button>
                            </div>
                        ` : '<span class="text-xs text-slate-400">-</span>'}
                    </td>
                </tr>
            `).join('');
        } else {
            invoicesTbody.innerHTML = `<tr><td colspan="6" class="px-6 py-8 text-center text-slate-400 font-medium bg-slate-50/50">No outstanding invoices.</td></tr>`;
        }
    }

    // Render Reminder Log
    const logContainer = document.getElementById('crm-reminder-log');
    if (logContainer) {
        if (data.reminder_log && data.reminder_log.length > 0) {
            logContainer.innerHTML = data.reminder_log.map(entry => `
                <div class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors border border-transparent hover:border-slate-100">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                            <span class="material-symbols-outlined text-sm">send</span>
                        </div>
                        <div>
                            <p class="text-sm font-bold text-charcoal dark:text-white">${entry.masked_name}</p>
                            <p class="text-xs text-slate-400">${formatDate(entry.date)}</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider bg-blue-50 text-blue-700">${entry.type.replace('_', ' ')}</span>
                        <p class="text-[10px] text-slate-400 mt-1">${entry.channel}</p>
                    </div>
                </div>
            `).join('');
        } else {
            logContainer.innerHTML = `<div class="text-center text-slate-400 font-medium py-4">No reminders sent yet.</div>`;
        }
    }
}

function onAgentFilterChange() {
    const select = document.getElementById('crm-agent-select');
    if (select) {
        crmDataLoaded = false;
        loadCRMData(select.value || null);
        loadFollowups(select.value || null);
    }
}

function openReminderModal(patientReferral, reminderType, maskedName) {
    document.getElementById('reminder-referral').value = patientReferral;
    document.getElementById('reminder-type').value = reminderType;
    document.getElementById('reminder-patient-name').innerText = maskedName;

    const typeLabel = reminderType === 'quote_pending'
        ? 'Outstanding Quote Reminder'
        : 'Overdue Invoice Reminder';
    document.getElementById('reminder-type-label').innerText = typeLabel;

    const modal = document.getElementById('reminder-modal');
    if (modal) modal.classList.add('active');
}

function closeReminderModal() {
    const modal = document.getElementById('reminder-modal');
    if (modal) modal.classList.remove('active');
}

async function confirmSendReminder() {
    const referral = document.getElementById('reminder-referral').value;
    const reminderType = document.getElementById('reminder-type').value;
    const btn = document.getElementById('confirm-reminder-btn');
    const originalText = btn.innerHTML;

    if (!referral || !reminderType) return;

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Sending...';

        await apiCall('koraflow_core.api.sales_agent_dashboard.send_patient_reminder', {
            patient_referral: referral, reminder_type: reminderType
        });

        closeReminderModal();
        const successModal = document.getElementById('success-modal');
        if (successModal) {
            successModal.classList.add('active');
            const title = document.querySelector('#success-modal h2');
            const msg = document.querySelector('#success-modal p');
            const detailsBox = document.querySelector('#success-modal .bg-slate-50');
            if (title) title.innerText = 'Reminder Sent!';
            if (msg) msg.innerText = 'The patient has been sent a POPIA-compliant reminder email.';
            if (detailsBox) detailsBox.classList.add('hidden');
        }
        crmDataLoaded = false;
        const agentSelect = document.getElementById('crm-agent-select');
        loadCRMData(agentSelect?.value || null);
    } catch (error) {
        console.error('Error sending reminder:', error);
        alert('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Support Ticket Functions
function openSupportModal() {
    console.log('Opening Support Modal');
    const modal = document.getElementById('support-ticket-modal');
    if (modal) {
        modal.classList.add('active');
        setTimeout(() => document.getElementById('ticket-subject')?.focus(), 100);
    } else {
        console.error('Support modal element not found!');
    }
}

function closeSupportModal() {
    const modal = document.getElementById('support-ticket-modal');
    if (modal) {
        modal.classList.remove('active');
        document.getElementById('ticket-subject').value = '';
        document.getElementById('ticket-description').value = '';
    }
}

async function submitSupportTicket() {
    const btn = document.querySelector('#support-ticket-modal button[onclick="submitSupportTicket()"]');
    const originalText = btn.innerHTML;

    const subject = document.getElementById('ticket-subject').value;
    const description = document.getElementById('ticket-description').value;

    if (!subject || !description) {
        alert('Please fill in all fields');
        return;
    }

    try {
        btn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Submitting...';
        btn.disabled = true;

        await apiCall('koraflow_core.api.sales_agent_dashboard.create_support_ticket', {
            subject: subject, description: description
        });

        closeSupportModal();
        const successModal = document.getElementById('success-modal');
        if (successModal) {
            successModal.classList.add('active');
            const title = document.querySelector('#success-modal h2');
            const msg = document.querySelector('#success-modal p');
            const detailsBox = document.querySelector('#success-modal .bg-slate-50');
            if (title) title.innerText = 'Ticket Submitted!';
            if (msg) msg.innerText = 'Your support ticket has been created. Our team will contact you shortly.';
            if (detailsBox) detailsBox.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error creating ticket:', error);
        alert('Connection error. Please try again.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// ========== FOLLOW-UPS & ACTIVITY FUNCTIONS ==========

async function loadFollowups(agentFilter) {
    try {
        if (!agentFilter && window._followupsData && Object.keys(window._followupsData).length > 0) {
            const data = window._followupsData;
            window._followupsData = null;
            renderFollowups(data?.followups || []);
        } else {
            const args = agentFilter ? { agent_filter: agentFilter } : {};
            const data = await apiCall('koraflow_core.api.sales_agent_dashboard.get_followups_due', args);
            renderFollowups(data?.followups || []);
        }
    } catch (error) {
        console.error('Error loading follow-ups:', error);
        renderFollowups([]);
    }
}

function renderFollowups(followups) {
    const container = document.getElementById('followups-container');
    const badge = document.getElementById('followup-count-badge');

    if (badge) {
        const overdueCount = followups.filter(f => f.is_overdue).length;
        const todayCount = followups.filter(f => f.is_today).length;
        const total = followups.length;
        if (overdueCount > 0) {
            badge.textContent = `${overdueCount} Overdue`;
            badge.className = 'px-2 py-1 bg-red-100 text-red-800 text-xs font-bold rounded uppercase tracking-wider';
        } else if (todayCount > 0) {
            badge.textContent = `${todayCount} Today`;
            badge.className = 'px-2 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded uppercase tracking-wider';
        } else {
            badge.textContent = `${total} Pending`;
            badge.className = 'px-2 py-1 bg-purple-100 text-purple-800 text-xs font-bold rounded uppercase tracking-wider';
        }
    }

    if (!container) return;

    if (followups.length === 0) {
        container.innerHTML = `<div class="px-6 py-8 text-center text-slate-400 font-medium">No follow-ups scheduled. Use "Log Activity" on any referral to set one.</div>`;
        return;
    }

    container.innerHTML = followups.map(fu => {
        let dateLabel = '';
        let dateBg = '';

        if (fu.is_overdue) {
            dateBg = 'bg-red-50/50 dark:bg-red-900/10';
            dateLabel = `<span class="text-red-600 font-bold">${Math.abs(fu.days_until)}d overdue</span>`;
        } else if (fu.is_today) {
            dateBg = 'bg-amber-50/50';
            dateLabel = `<span class="text-amber-600 font-bold">Today</span>`;
        } else {
            dateLabel = `<span class="text-slate-500">In ${fu.days_until}d</span>`;
        }

        return `
            <div class="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors ${dateBg}">
                <div class="w-10 h-10 rounded-full ${fu.is_overdue ? 'bg-red-100' : fu.is_today ? 'bg-amber-100' : 'bg-purple-100'} flex items-center justify-center flex-shrink-0">
                    <span class="material-symbols-outlined text-sm ${fu.is_overdue ? 'text-red-600' : fu.is_today ? 'text-amber-600' : 'text-purple-600'}">event</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-charcoal dark:text-white">${fu.masked_name}</span>
                        <span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-slate-100 text-slate-500 uppercase tracking-wider">${fu.status}</span>
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="text-xs ${fu.is_overdue ? 'text-red-600 font-bold' : fu.is_today ? 'text-amber-600 font-bold' : 'text-slate-500'}">${formatDate(fu.followup_date)}</span>
                        <span class="text-xs text-slate-300">&middot;</span>
                        ${dateLabel}
                    </div>
                    ${fu.followup_note ? `<p class="text-xs text-slate-400 mt-1 truncate">${fu.followup_note}</p>` : ''}
                    ${fu.last_activity_note ? `<p class="text-[10px] text-slate-400 mt-0.5 truncate italic">Last: ${fu.last_activity_note}</p>` : ''}
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                    <button onclick="openActivityModal('${fu.referral}', '${fu.masked_name}')"
                        class="px-3 py-1.5 text-xs font-bold rounded-lg bg-primary/10 text-charcoal hover:bg-primary/20 transition-all flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">edit_note</span>
                        Log
                    </button>
                    <button onclick="openTimelineModal('${fu.referral}')"
                        class="px-3 py-1.5 text-xs font-bold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-all flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">timeline</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// ========== ACTIVITY MODAL ==========

function openActivityModal(patientReferral, maskedName) {
    document.getElementById('activity-referral').value = patientReferral;
    document.getElementById('activity-patient-label').innerText = maskedName;
    document.getElementById('activity-note').value = '';
    document.getElementById('activity-followup-date').value = '';
    document.getElementById('activity-type-value').value = 'Note';

    // Reset type buttons
    document.querySelectorAll('.activity-type-btn').forEach(btn => {
        btn.classList.remove('active-activity-type');
    });
    // Set "Note" as default active
    const noteBtn = document.querySelector('.activity-type-btn:nth-child(5)');
    if (noteBtn) noteBtn.classList.add('active-activity-type');

    const modal = document.getElementById('activity-modal');
    if (modal) modal.classList.add('active');
    setTimeout(() => document.getElementById('activity-note')?.focus(), 100);
}

function closeActivityModal() {
    const modal = document.getElementById('activity-modal');
    if (modal) modal.classList.remove('active');
}

function selectActivityType(btnEl, type) {
    document.querySelectorAll('.activity-type-btn').forEach(btn => {
        btn.classList.remove('active-activity-type');
    });
    btnEl.classList.add('active-activity-type');
    document.getElementById('activity-type-value').value = type;
}

async function submitActivity() {
    const referral = document.getElementById('activity-referral').value;
    const activityType = document.getElementById('activity-type-value').value;
    const note = document.getElementById('activity-note').value;
    const followupDate = document.getElementById('activity-followup-date').value;
    const btn = document.getElementById('submit-activity-btn');
    const originalText = btn.innerHTML;

    if (!note.trim()) {
        alert('Please enter an activity note');
        return;
    }

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Saving...';

        const payload = {
            patient_referral: referral,
            activity_type: activityType,
            note: note
        };
        if (followupDate) {
            payload.followup_date = followupDate;
        }

        await apiCall('koraflow_core.api.sales_agent_dashboard.log_activity', payload);

        closeActivityModal();
        const successModal = document.getElementById('success-modal');
        if (successModal) {
            successModal.classList.add('active');
            const title = document.querySelector('#success-modal h2');
            const msg = document.querySelector('#success-modal p');
            const detailsBox = document.querySelector('#success-modal .bg-slate-50');
            if (title) title.innerText = 'Activity Logged!';
            if (msg) msg.innerText = followupDate
                ? `Activity logged and follow-up scheduled for ${formatDate(followupDate)}.`
                : 'Activity logged successfully.';
            if (detailsBox) detailsBox.classList.add('hidden');
        }

        const agentSelect = document.getElementById('crm-agent-select');
        loadFollowups(agentSelect?.value || null);
        crmDataLoaded = false;
        loadCRMData(agentSelect?.value || null);

        if (document.getElementById('timeline-modal')?.classList.contains('active')) {
            loadTimeline(referral);
        }
    } catch (error) {
        console.error('Error logging activity:', error);
        alert('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ========== TIMELINE MODAL ==========

let currentTimelineReferral = null;

function openTimelineModal(patientReferral) {
    currentTimelineReferral = patientReferral;
    const modal = document.getElementById('timeline-modal');
    if (modal) modal.classList.add('active');
    loadTimeline(patientReferral);
}

function closeTimelineModal() {
    const modal = document.getElementById('timeline-modal');
    if (modal) modal.classList.remove('active');
    currentTimelineReferral = null;
}

function openActivityFromTimeline() {
    if (!currentTimelineReferral) return;
    const name = document.getElementById('timeline-patient-name')?.innerText || 'Patient';
    openActivityModal(currentTimelineReferral, name);
}

async function loadTimeline(patientReferral) {
    const entriesContainer = document.getElementById('timeline-entries');
    if (entriesContainer) {
        entriesContainer.innerHTML = '<div class="text-center text-slate-400 font-medium py-4">Loading timeline...</div>';
    }

    try {
        const data = await apiCall('koraflow_core.api.sales_agent_dashboard.get_patient_activity', { patient_referral: patientReferral });
        if (data) renderTimeline(data);
    } catch (error) {
        console.error('Error loading timeline:', error);
        if (entriesContainer) {
            entriesContainer.innerHTML = '<div class="text-center text-red-500 font-medium py-4">Error loading timeline.</div>';
        }
    }
}

function renderTimeline(data) {
    // Update header
    setText('timeline-patient-name', data.masked_name || 'Patient');
    const statusBadge = document.getElementById('timeline-status-badge');
    if (statusBadge) statusBadge.textContent = data.current_status || 'Unknown';

    const followupBadge = document.getElementById('timeline-followup-badge');
    if (followupBadge) {
        if (data.next_followup_date) {
            followupBadge.classList.remove('hidden');
            followupBadge.textContent = `Follow-up: ${formatDate(data.next_followup_date)}`;
        } else {
            followupBadge.classList.add('hidden');
        }
    }

    // Update Log button referral
    const logBtn = document.getElementById('timeline-log-btn');
    if (logBtn) {
        logBtn.onclick = () => openActivityModal(data.referral, data.masked_name);
    }

    // Render timeline entries
    const container = document.getElementById('timeline-entries');
    if (!container) return;

    if (!data.timeline || data.timeline.length === 0) {
        container.innerHTML = '<div class="text-center text-slate-400 font-medium py-8">No activity recorded yet. Click "Log New Activity" to get started.</div>';
        return;
    }

    const iconMap = {
        'Call': { icon: 'call', color: 'bg-green-100 text-green-600' },
        'WhatsApp': { icon: 'chat', color: 'bg-emerald-100 text-emerald-600' },
        'Email': { icon: 'mail', color: 'bg-blue-100 text-blue-600' },
        'Meeting': { icon: 'groups', color: 'bg-indigo-100 text-indigo-600' },
        'Note': { icon: 'edit_note', color: 'bg-slate-100 text-slate-600' },
        'Other': { icon: 'more_horiz', color: 'bg-slate-100 text-slate-600' },
    };

    const reminderStyle = { icon: 'send', color: 'bg-amber-100 text-amber-600' };
    const messageStyle = { icon: 'chat_bubble', color: 'bg-purple-100 text-purple-600' };

    container.innerHTML = `<div class="timeline-line"></div>` + data.timeline.map((entry, idx) => {
        let style;
        if (entry.icon === 'reminder') {
            style = reminderStyle;
        } else if (entry.icon === 'message') {
            style = messageStyle;
        } else {
            style = iconMap[entry.type] || iconMap['Note'];
        }

        return `
            <div class="relative flex gap-4 pb-6">
                <div class="w-10 h-10 rounded-full ${style.color} flex items-center justify-center flex-shrink-0 z-10 border-2 border-white dark:border-slate-900">
                    <span class="material-symbols-outlined text-sm">${style.icon}</span>
                </div>
                <div class="flex-1 pt-1">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs font-bold text-charcoal dark:text-white uppercase tracking-wider">${entry.type}</span>
                        <span class="text-[10px] text-slate-400">${formatDate(entry.date)}</span>
                    </div>
                    <p class="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">${entry.note}</p>
                </div>
            </div>
        `;
    }).join('');
}
