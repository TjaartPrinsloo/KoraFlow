console.log("KoraFlow: patient.js loaded - Version 5.3 (Final Clean)");

frappe.ui.form.on('Patient', {
    refresh: function (frm) {
        // Visual confirmation for the user
        if (!window._koraflow_notified || window._koraflow_notified < 8) {
            frappe.show_alert({ message: __("KoraFlow Patient Script v5.3 Active"), indicator: 'blue' });
            window._koraflow_notified = (window._koraflow_notified || 0) + 1;
        }

        if (!frm.doc.__islocal) {
            // Standard Buttons and Actions
            frm.add_custom_button(__('Allow Intake Retake'), function () {
                frappe.confirm(
                    __('Are you sure you want to allow this patient to retake the intake form?'),
                    function () {
                        frappe.call({
                            method: 'frappe.client.set_value',
                            args: {
                                doctype: 'Patient',
                                name: frm.doc.name,
                                fieldname: 'custom_allow_intake_retake',
                                value: 1
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Intake retake enabled for this patient.'));
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            });

            frm.page.add_inner_button(__('Print Latest Intake Form'), function () {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'GLP-1 Intake Submission',
                        filters: { patient: frm.doc.name },
                        fields: ['name'],
                        limit_page_length: 1,
                        order_by: 'creation desc'
                    },
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            frappe.utils.print(
                                'GLP-1 Intake Submission',
                                r.message[0].name,
                                'Intake Form',
                                0,
                                frm.doc.language || 'en'
                            );
                        } else {
                            frappe.msgprint(__('No Intake Form found for this patient.'));
                        }
                    }
                });
            }).addClass('btn-primary').css({ 'color': 'white', 'background-color': '#248FF1' });
        }

        // Intake Form History
        if (!frm.doc.__islocal && frm.get_field('glp1_intake_forms_html')) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'GLP-1 Intake Submission',
                    filters: { patient: frm.doc.name },
                    fields: ['name', 'creation'],
                    order_by: 'creation desc'
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let html = '<div class="intake-forms-wrapper" style="margin-bottom: 30px;">';
                        html += '<table class="table table-bordered table-hover">';
                        html += '<thead><tr><th>' + __("Submission ID") + '</th><th>' + __("Date") + '</th></tr></thead><tbody>';
                        r.message.forEach(d => {
                            html += '<tr style="cursor: pointer;" onclick="frappe.set_route(\'Form\', \'GLP-1 Intake Submission\', \'' + d.name + '\')">';
                            html += '<td><a href="/app/glp-1-intake-submission/' + d.name + '"><b>' + d.name + '</b></a></td>';
                            html += '<td>' + frappe.datetime.global_date_format(d.creation) + '</td>';
                            html += '</tr>';
                        });
                        html += '</tbody></table></div>';
                        frm.get_field('glp1_intake_forms_html').$wrapper.html(html);
                    } else {
                        frm.get_field('glp1_intake_forms_html').$wrapper.html('<div class="text-muted">' + __("No GLP-1 Intake Submissions found.") + '</div>');
                    }
                }
            });
        }

        // Support Tickets
        if (!frm.doc.__islocal) {
            frm.dashboard.add_section(
                '<div class="support-tickets-section"> \
                    <div class="header flex justify-between items-center mb-4"> \
                        <h6 class="m-0">' + __("Recent Support Tickets") + '</h6> \
                        <button class="btn btn-xs btn-default py-1" id="btn-new-ticket">' + __("New Ticket") + '</button> \
                    </div> \
                    <div id="support-tickets-list" class="text-muted small">' + __("Loading...") + '</div> \
                </div>',
                __('Clinical Support')
            );

            $('#btn-new-ticket').on('click', function () {
                const d = new frappe.ui.Dialog({
                    title: __('Create Support Ticket'),
                    fields: [
                        { label: __('Subject'), fieldname: 'subject', fieldtype: 'Data', reqd: 1 },
                        { label: __('Category'), fieldname: 'category', fieldtype: 'Select', options: ['Billing/Payments', 'Side Effects', 'Prescriptions', 'Delivery', 'Other'], default: 'Other' },
                        { label: __('Description'), fieldname: 'description', fieldtype: 'Small Text', reqd: 1 }
                    ],
                    primary_action_label: __('Create'),
                    primary_action(values) {
                        frappe.call({
                            method: 'koraflow_core.api.support.create_patient_support_ticket_from_desk',
                            args: {
                                patient: frm.doc.name,
                                subject: values.subject,
                                description: values.description,
                                category: values.category
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    d.hide();
                                    frappe.show_alert({ message: __('Ticket created'), indicator: 'green' });
                                    render_tickets();
                                }
                            }
                        });
                    }
                });
                d.show();
            });

            const render_tickets = function () {
                frappe.call({
                    method: 'koraflow_core.api.support.get_support_history_for_desk',
                    args: { patient: frm.doc.name },
                    callback: function (r) {
                        const tickets = r.message || [];
                        let html = '';
                        if (tickets.length > 0) {
                            html = '<table class="table table-hover table-condensed"> \
                                <thead> \
                                    <tr> \
                                        <th>' + __("Subject") + '</th> \
                                        <th>' + __("Status") + '</th> \
                                        <th>' + __("Created") + '</th> \
                                    </tr> \
                                </thead> \
                                <tbody>';
                            tickets.forEach(t => {
                                const status_class = t.status === 'Open' ? 'text-warning' : (t.status === 'Closed' ? 'text-success' : 'text-info');
                                html += '<tr style="cursor: pointer" onclick="frappe.set_route(\'Form\', \'Issue\', \'' + t.name + '\')"> \
                                    <td>' + t.subject + '</td> \
                                    <td class="' + status_class + '"><b>' + t.status + '</b></td> \
                                    <td>' + frappe.datetime.global_date_format(t.creation) + '</td> \
                                </tr>';
                            });
                            html += '</tbody></table>';
                        } else {
                            html = '<div class="text-center p-4">' + __("No support tickets found for this patient.") + '</div>';
                        }
                        $('#support-tickets-list').html(html);
                    }
                });
            };
            render_tickets();
        }

        // --- UI CUSTOMIZATION ENGINE ---
        if (!frm.doc.__islocal) {
            const applyUI = () => {
                if (frm.doc.__islocal) return;

                // 1. UNIVERSAL: ALWAYS REVEAL AGENT DROP-DOWNS
                // Force section visibility first
                frm.set_df_property('customer_details_section', 'hidden', 0);
                frm.toggle_display('customer_details_section', true);
                
                // jQuery override for the section itself
                let section = frm.get_field('customer_details_section');
                if (section && section.$wrapper) {
                    section.$wrapper.attr('style', 'display: block !important;');
                }

                ['referred_by_sales_agent', 'custom_sales_agent', 'custom_referrer_name'].forEach(fieldname => {
                    let field = frm.get_field(fieldname);
                    if (field) {
                        console.log(`KoraFlow: Forcing visibility for field: ${fieldname}`);

                        frm.set_df_property(fieldname, 'hidden', 0);
                        frm.set_df_property(fieldname, 'read_only', 0);
                        frm.toggle_display(fieldname, true);
                        frm.toggle_enable(fieldname, true);

                        if (field.df) {
                            field.df.hidden = 0;
                            field.df.read_only = 0;
                            field.refresh();
                        }
                        frm.refresh_field(fieldname);

                        // AGGRESSIVE jQuery OVERRIDE - Targeting the wrapper specifically
                        if (field.$wrapper) {
                            field.$wrapper.show().attr('style', 'display: block !important;');
                            // Also ensure the parent columns are visible
                            field.$wrapper.closest('.form-column').show().attr('style', 'display: block !important;');
                            field.$wrapper.closest('.section-body').show().attr('style', 'display: block !important;');
                        }
                    }
                });

                // 2. ROLE-SPECIFIC: NURSE / ADMIN TAILORING
                if (frappe.user_roles && (frappe.user_roles.includes('Nurse') || frappe.user_roles.includes('System Manager'))) {
                    // Hide bloated sections BUT NOT customer_details_section anymore
                    ['activity_section', 'stats_section', 'billing_section', 'connections_section'].forEach(s => {
                        if (s !== 'customer_details_section') {
                            frm.set_df_property(s, 'hidden', 1);
                        }
                    });

                    // Hide standard fields that nurses don't use
                    ['customer', 'customer_group', 'territory', 'default_currency', 'default_price_list', 'language'].forEach(f => {
                        frm.set_df_property(f, 'hidden', 1);
                        frm.toggle_display(f, false);
                    });

                    // Explicitly ensure the fields we want ARE shown for these roles
                    ['referred_by_sales_agent', 'custom_sales_agent', 'custom_referrer_name'].forEach(fieldname => {
                        frm.set_df_property(fieldname, 'hidden', 0);
                        frm.toggle_display(fieldname, true);
                    });

                    // Ensure Encounter button exists
                    if (!frm._encounter_button_added) {
                        try {
                            frm.add_custom_button(__('New Patient Encounter'), () => {
                                frappe.new_doc('Patient Encounter', {
                                    patient: frm.doc.name,
                                    patient_name: frm.doc.patient_name
                                });
                            }, __('Create'));
                            frm._encounter_button_added = true;
                        } catch (e) { }
                    }
                }
            };

            // Multi-pass to overcome latent standard scripts
            setTimeout(applyUI, 100);
            setTimeout(applyUI, 1000);
            setTimeout(applyUI, 3000);
        }
    }
});
