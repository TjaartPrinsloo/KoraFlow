console.log("KoraFlow: patient.js loaded - Version 5.3 (Final Clean)");

frappe.ui.form.on('Patient', {
    refresh: function (frm) {
        // Visual confirmation for the user
        if (!window._koraflow_notified || window._koraflow_notified < 8) {
            frappe.show_alert({ message: __("KoraFlow Patient Script v5.3 Active"), indicator: 'blue' });
            window._koraflow_notified = (window._koraflow_notified || 0) + 1;
        }

        // Show returning patient banner prominently for nurses
        if (!frm.doc.__islocal && frm.doc.custom_is_existing_patient) {
            frm.dashboard.add_comment(
                __('This patient self-identified as a <b>returning Slim2Well patient</b> during intake. Please verify their previous treatment history.'),
                'orange',
                true
            );
            // Also add a visual indicator at the top
            if (!frm._existing_patient_banner) {
                frm._existing_patient_banner = true;
                $(frm.fields_dict.patient_name?.wrapper || frm.wrapper).find('.page-head').first().before(
                    '<div class="existing-patient-banner" style="background: #FFF3CD; border-left: 4px solid #FF9800; padding: 10px 16px; margin-bottom: 10px; border-radius: 4px; font-weight: 600; color: #856404;">' +
                    '<span style="margin-right: 6px;">&#9888;</span> Returning Patient — Previously treated at Slim2Well' +
                    '</div>'
                );
            }
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

        // --- FIX: Blood Group - hide standard field via CSS (immune to applyUI loop) ---
        if (!document.getElementById('kf-hide-blood-group')) {
            let style = document.createElement('style');
            style.id = 'kf-hide-blood-group';
            style.textContent = '[data-fieldname="blood_group"] { display: none !important; }';
            document.head.appendChild(style);
        }

        // --- FIX: Filter Assigned Nurse to only show users with Nurse role ---
        frm.set_query('custom_assigned_nurse', function () {
            return {
                query: 'koraflow_core.api.nurse_query.get_nurses'
            };
        });

        // --- FIX: Remove help text from height and BMI fields ---
        frm.set_df_property('intake_height_cm', 'description', '');
        frm.set_df_property('custom_bmi', 'description', '');
        frm.set_df_property('bmi', 'description', '');

        // --- UI CUSTOMIZATION ENGINE ---
        if (!frm.doc.__islocal) {
            const applyUI = () => {
                if (frm.doc.__islocal) return;

                // 1. UNIVERSAL: Hide Customer Details (now replaced by Referrals tab)
                frm.set_df_property('customer_details_section', 'hidden', 1);
                frm.toggle_display('customer_details_section', false);

                // Hide __newname rename field
                $(frm.wrapper).find('[data-fieldname="__newname"]').closest('.form-section').hide();

                // Ensure form is always in edit mode for users with write permission
                if (!frm.is_new() && frm.perm[0] && frm.perm[0].write) {
                    // This is the Frappe way to force edit mode
                    frm.amend_doc = false;
                    frm.page.set_primary_action(__('Save'), () => frm.save());
                    frm.enable_save();

                    // Force all fields into write/input mode (skip hidden fields)
                    frm.fields.forEach(field => {
                        if (field.df && field.df.fieldtype !== 'Section Break' &&
                            field.df.fieldtype !== 'Column Break' &&
                            field.df.fieldtype !== 'Tab Break' &&
                            field.df.fieldtype !== 'HTML' &&
                            !field.df.read_only &&
                            !field.df.hidden) {
                            field.disp_status = 'Write';
                            if (field.$wrapper) {
                                field.$wrapper.removeClass('hide-control');
                                field.$wrapper.find('.control-value').hide();
                                field.$wrapper.find('.control-input').show();
                            }
                            if (!field.has_input && field.make_input) {
                                field.make_input();
                            }
                        }
                    });

                    // Persistent save button
                    $(frm.wrapper).off('dirty.kf').on('dirty.kf', () => {
                        setTimeout(() => {
                            frm.enable_save();
                            frm.page.set_primary_action(__('Save'), () => frm.save());
                        }, 100);
                    });
                }

                // Force Referrals tab - Sales Partner field visible with input
                let spField = frm.get_field('custom_ref_sales_partner');
                if (spField) {
                    frm.set_df_property('custom_ref_sales_partner', 'hidden', 0);
                    frm.toggle_display('custom_ref_sales_partner', true);
                    if (!spField.has_input && spField.make_input) {
                        spField.make_input();
                    }
                    if (spField.$wrapper) {
                        spField.$wrapper.show().removeClass('hide-control').attr('style', 'display: block !important;');
                        spField.$wrapper.find('.control-label').text('Linked Sales Partner');
                        spField.$wrapper.find('.control-input').show();
                        spField.$wrapper.closest('.form-column').show().attr('style', 'display: block !important;');
                        spField.$wrapper.closest('.section-body').show().attr('style', 'display: block !important;');
                    }
                    frm.refresh_field('custom_ref_sales_partner');

                    // Override awesomplete to show all partners alphabetically
                    frm.set_query('custom_ref_sales_partner', function() {
                        return {
                            page_length: 0,
                            order_by: 'name asc'
                        };
                    });

                    // Pre-load all partners into the dropdown
                    frappe.call({
                        method: 'frappe.client.get_list',
                        args: {
                            doctype: 'Sales Partner',
                            fields: ['name'],
                            order_by: 'name asc',
                            limit_page_length: 0
                        },
                        async: false,
                        callback: function(r) {
                            if (r.message && spField.awesomplete) {
                                spField._all_partners = r.message.map(p => p.name);
                            }
                        }
                    });

                    // Override get_query_results to always show full list
                    if (spField.awesomplete) {
                        let origInput = spField.$input;
                        if (origInput) {
                            origInput.on('focus', function() {
                                if (spField._all_partners && spField.awesomplete) {
                                    let list = spField._all_partners.map(name => ({
                                        label: name,
                                        value: name
                                    }));
                                    spField.awesomplete.list = list;
                                    spField.awesomplete.evaluate();
                                    spField.awesomplete.open();
                                }
                            });
                        }
                    }
                }

                // 2. ROLE-SPECIFIC: NURSE / ADMIN TAILORING
                if (frappe.user_roles && (frappe.user_roles.includes('Nurse') || frappe.user_roles.includes('System Manager'))) {
                    // Hide bloated sections
                    ['activity_section', 'stats_section', 'billing_section', 'connections_section'].forEach(s => {
                        frm.set_df_property(s, 'hidden', 1);
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
