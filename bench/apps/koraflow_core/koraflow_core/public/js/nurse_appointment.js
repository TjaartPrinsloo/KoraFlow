// DocType: Patient Appointment — hide Payments section for Nurse users

frappe.ui.form.on('Patient Appointment', {
    refresh(frm) {
        if (frappe.user.has_role('Nurse') && !frappe.user.has_role('Physician') && !frappe.user.has_role('System Manager')) {
            // Hide the Payments section and all its fields
            frm.set_df_property('section_break_16', 'hidden', 1);
            frm.set_df_property('mode_of_payment', 'hidden', 1);
            frm.set_df_property('billing_item', 'hidden', 1);
            frm.set_df_property('invoiced', 'hidden', 1);
            frm.set_df_property('paid_amount', 'hidden', 1);
            frm.set_df_property('ref_sales_invoice', 'hidden', 1);
        }
    }
});
