frappe.ui.form.on("GLP-1 Pharmacy Dispense Task", {
    refresh(frm) {
        // Only show action buttons for Pending/In Progress tasks
        if (frm.doc.status === "Pending" || frm.doc.status === "In Progress") {

            // Print Pick Slip — inline button (not in dropdown)
            frm.page.add_inner_button(__("Print Pick Slip"), function() {
                const url = `/api/method/koraflow_core.api.dispensing.get_pick_slip?task_name=${frm.doc.name}`;
                window.open(url, "_blank");
            }).addClass("btn-default");

            // Dispense & Ship — inline primary button
            frm.page.add_inner_button(__("Dispense & Ship"), function() {
                frappe.confirm(
                    __("This will:<br>• Deduct stock from warehouse<br>• Book the courier for collection<br>• Mark prescription as dispensed<br><br>Have you verified all items against the prescription?"),
                    function() {
                        frm.call("dispense_and_ship", {}).then(r => {
                            if (r.message && r.message.success) {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: "green"
                                });
                                frm.reload_doc();
                            } else {
                                frappe.show_alert({
                                    message: r.message ? r.message.message : __("Error during dispense"),
                                    indicator: "red"
                                });
                            }
                        });
                    }
                );
            }).addClass("btn-primary");
        }

        // Show linked documents
        if (frm.doc.delivery_note) {
            frm.set_intro(__("Delivery Note: {0} (Draft — will be submitted on dispense)", [frm.doc.delivery_note]));
        }

        // Mark as In Progress when pharmacist opens it
        if (frm.doc.status === "Pending" && !frm.is_new()) {
            frm.set_value("status", "In Progress");
            frm.save_or_update();
        }
    }
});
