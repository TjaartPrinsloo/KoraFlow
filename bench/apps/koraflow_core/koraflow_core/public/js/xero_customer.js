frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Show Xero banner and action buttons for Xero-imported customers
        if (frm.doc.custom_is_xero_customer && !frm.is_new()) {
            // Show banner
            var banner_msg = '';
            if (!frm.doc.custom_intake_completed && frm.doc.custom_intake_required) {
                banner_msg = __('Imported from Xero — Intake form required but not completed');
                frm.dashboard.set_headline_alert(
                    '<div class="alert alert-warning" style="margin-bottom:0">' +
                    '<i class="fa fa-exclamation-triangle"></i> ' + banner_msg +
                    '</div>'
                );
            } else if (frm.doc.custom_intake_completed) {
                banner_msg = __('Imported from Xero — Intake form completed');
                frm.dashboard.set_headline_alert(
                    '<div class="alert alert-info" style="margin-bottom:0">' +
                    '<i class="fa fa-check-circle"></i> ' + banner_msg +
                    '</div>'
                );
            }

            // Check if user has a linked portal account
            if (frm.doc.email_id) {
                frappe.call({
                    method: 'frappe.client.get_count',
                    args: {
                        doctype: 'User',
                        filters: { email: frm.doc.email_id, enabled: 1 }
                    },
                    callback: function(r) {
                        if (!r.message || r.message === 0) {
                            // No user account — show create button
                            frm.add_custom_button(__('Create User Account'), function() {
                                create_user_account(frm);
                            }, __('Xero Customer'));
                        }
                    }
                });
            } else {
                frm.add_custom_button(__('Create User Account'), function() {
                    frappe.prompt({
                        fieldname: 'email',
                        label: __('Customer Email'),
                        fieldtype: 'Data',
                        options: 'Email',
                        reqd: 1
                    }, function(values) {
                        frm.set_value('email_id', values.email);
                        frm.save().then(function() {
                            create_user_account(frm);
                        });
                    }, __('Enter Customer Email'), __('Create'));
                }, __('Xero Customer'));
            }

            // Send Intake Form button (only if intake not completed)
            if (frm.doc.custom_intake_required && !frm.doc.custom_intake_completed) {
                frm.add_custom_button(__('Send Intake Form'), function() {
                    send_intake_form(frm);
                }, __('Xero Customer'));
            }
        }
    }
});


function create_user_account(frm) {
    frappe.call({
        method: 'koraflow_core.api.xero_customer.create_user_for_xero_customer',
        args: {
            customer_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Creating user account and patient record...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Account Created'),
                    indicator: 'green',
                    message: __('User account created for {0}. A welcome email has been sent.', [frm.doc.email_id])
                });
                frm.reload_doc();
            }
        }
    });
}


function send_intake_form(frm) {
    frappe.call({
        method: 'koraflow_core.api.xero_customer.send_intake_form',
        args: {
            customer_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Sending intake form...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Intake Form Sent'),
                    indicator: 'green',
                    message: __('Intake form has been sent to {0}.', [frm.doc.email_id])
                });
            }
        }
    });
}
