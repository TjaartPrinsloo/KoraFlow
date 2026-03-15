
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
        const response = await fetch('/api/method/koraflow_core.api.sales_agent_dashboard.get_dashboard_data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': window.csrf_token
            }
        });

        const data = await response.json();

        if (data.message) {
            updateDashboardUI(data.message);
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
        // Using pending as available for now based on logic
        const balanceValue = summary.pending || 0;
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
                    <span class="text-[10px] font-bold uppercase tracking-wider ${comm.status === 'Paid' ? 'text-green-600' : 'text-slate-400'}">${comm.status}</span>
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

    const amount = amountEl.value;
    const notes = notesEl ? notesEl.value : '';

    if (amount <= 0) {
        alert('Please enter a valid amount');
        return;
    }

    try {
        const response = await fetch('/api/method/frappe.client.insert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': window.csrf_token
            },
            body: JSON.stringify({
                doc: {
                    doctype: "Sales Agent Payout Request",
                    amount: amount,
                    // withdrawal_amount: amount, // obsolete field
                    notes: notes,
                    sales_agent: window.sales_agent_doc_name || window.sales_agent_id,
                    status: "Pending"
                }
            })
        });

        const result = await response.json();

        if (response.ok && !result.exc) {
            closePayoutModal();

            // Show success modal
            const successModal = document.getElementById('success-modal');
            if (successModal) successModal.classList.add('active');

            // Update success modal details
            const reqId = document.getElementById('request-id');
            const reqAmt = document.getElementById('request-amount');

            if (reqId && result.message) reqId.innerText = result.message.name;
            if (reqAmt) reqAmt.innerText = formatCurrency(amount);

            // Refresh dashboard data
            loadDashboardData();
        } else {
            console.error('Error submitting payout:', result);
            alert('Failed to submit payout request. ' + (result._server_messages ? 'Server error.' : ''));
        }
    } catch (error) {
        console.error('Error submitting payout:', error);
        alert('An error occurred. Please check your connection.');
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

        const response = await fetch('/api/method/koraflow_core.api.sales_agent_dashboard.create_referral', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': window.csrf_token
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email: email,
                mobile_no: mobile
            })
        });

        const result = await response.json();

        if (response.ok) {
            closeNewReferralModal();
            // Show success modal reuse or simple alert? reusing success modal is better UX
            // Retooling success modal for generic success messages usage
            const successModal = document.getElementById('success-modal');
            if (successModal) {
                successModal.classList.add('active');
                // Reset modal content
                document.querySelector('#success-modal h2').innerText = 'Referral Created!';
                document.querySelector('#success-modal p').innerText = `Successfully created referral for ${firstName} ${lastName}.`;

                // Hide irrelevant parts for referral success
                const detailsBox = document.querySelector('#success-modal .bg-slate-50');
                if (detailsBox) detailsBox.classList.add('hidden');

                // Reload dashboard
                loadDashboardData();
            } else {
                alert('Referral created successfully!');
                loadDashboardData();
            }
        } else {
            alert('Failed to create referral: ' + (result.exc || result.message || 'Unknown error'));
        }
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

        const response = await fetch('/api/method/koraflow_core.api.sales_agent_dashboard.create_support_ticket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': window.csrf_token
            },
            body: JSON.stringify({
                subject: subject,
                description: description
            })
        });

        const result = await response.json();

        if (response.ok) {
            closeSupportModal();

            // Reuse Success Modal
            const successModal = document.getElementById('success-modal');
            if (successModal) {
                successModal.classList.add('active');

                // Customize content
                const title = document.querySelector('#success-modal h2');
                const msg = document.querySelector('#success-modal p');
                const detailsBox = document.querySelector('#success-modal .bg-slate-50');

                if (title) title.innerText = 'Ticket Submitted!';
                if (msg) msg.innerText = 'Your support ticket has been created. Our team will contact you shortly.';
                if (detailsBox) detailsBox.classList.add('hidden');

            } else {
                alert('Support ticket created successfully!');
            }
        } else {
            alert('Failed to submit ticket: ' + (result.exc || result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating ticket:', error);
        alert('Connection error. Please try again.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
