frappe.ui.form.on('GLP-1 Intake Review', {
    refresh: function (frm) {
        if (frm.doc.intake_submission) {
            frm.add_custom_button(__('Print Intake Form'), function () {
                frappe.utils.print(
                    'GLP-1 Intake Submission',
                    frm.doc.intake_submission,
                    'Intake Form',
                    0,
                    frm.doc.language
                );
            }).addClass('btn-primary');
        }
    }
});
