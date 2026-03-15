// DocType: Patient Encounter | Script Type: Form

frappe.ui.form.on('Patient Encounter', {
    refresh(frm) {
        if (frappe.user.has_role('Nurse')) {

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
        if (frappe.user.has_role('Nurse')) {
            frappe.throw(__('Only a Doctor can submit a Patient Encounter.'));
            frappe.validated = false;
        }
    }
});
