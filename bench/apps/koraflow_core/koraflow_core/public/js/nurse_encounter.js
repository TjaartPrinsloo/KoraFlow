// DocType: Patient Encounter | Script Type: Form

frappe.ui.form.on('Patient Encounter', {
    refresh(frm) {
        // Doctors (Physician role) bypass all nurse restrictions
        var is_physician = frappe.user.has_role('Physician');
        var is_nurse = frappe.user.has_role('Nurse');

        // Hide sections for both nurses and doctors (not admin)
        if (is_nurse && !frappe.user.has_role('System Manager')) {
            var hidden_fields = [
                'invoiced',                // Invoiced checkbox
                'codification',            // Medical Coding section
                'codification_table',      // Medical Coding table
                'sb_test_prescription',    // Investigations section
                'lab_test_prescription',   // Lab Tests table
                'sb_procedures',           // Procedures section
                'procedure_prescription',  // Clinical Procedures table
                'rehabilitation_section'   // Rehabilitation section
            ];
            hidden_fields.forEach(function(f) {
                frm.set_df_property(f, 'hidden', 1);
            });
        }

        // Nurse-only restrictions (not doctors)
        if (is_nurse && !is_physician) {

            // Hard hide the Submit button
            frm.page.clear_primary_action();

            // Replace with a clean "Save Draft" primary action
            frm.page.set_primary_action(__('Save Draft'), () => {
                frm.save('Save');
            }, 'save');

            // Show a clear status banner so nurse knows what to expect
            if (frm.doc.docstatus === 0) {
                frm.dashboard.add_comment(
                    '📝 Saved as Draft — A Doctor must review and submit this encounter.',
                    'yellow',
                    true
                );
            }

            // Hide the Actions menu entirely (contains Submit inside)
            frm.page.btn_secondary.hide();
        }
    },

    // Prevent accidental submit via keyboard shortcuts or other triggers
    before_submit(frm) {
        if (frappe.user.has_role('Nurse') && !frappe.user.has_role('Physician')) {
            frappe.throw(__('Only a Doctor can submit a Patient Encounter.'));
            frappe.validated = false;
        }
    }
});
