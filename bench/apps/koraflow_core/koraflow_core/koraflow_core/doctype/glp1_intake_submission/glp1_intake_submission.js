frappe.ui.form.on('GLP-1 Intake Submission', {
    refresh: function (frm) {
        // Add "Print Intake Form" button to the form dashboard or as a primary action
        if (!frm.is_new()) {
            frm.add_custom_button(__('Print Intake Form'), function () {
                // Open PDF for the specific Print Format
                const url = frappe.utils.get_url_to_report(
                    'GLP-1 Intake Submission',
                    frm.doc.name,
                    'Intake Form'
                );
                // Actually, the standard way in Frappe is to use frappe.utils.print
                frappe.utils.print(
                    frm.doctype,
                    frm.docname,
                    'Intake Form',
                    0, // Letterhead
                    frm.doc.language
                );
            }).addClass('btn-primary');
        }
    }
});
