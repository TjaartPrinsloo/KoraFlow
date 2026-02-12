// Copyright (c) 2024, KoraFlow Team and contributors
// For license information, please see license.txt

frappe.ui.form.on("Xero Settings", {
    refresh: function (frm) {
        if (frm.doc.connection_status === "Connected") {
            frm.set_df_property("connect_to_xero", "label", "Reconnect to Xero");
        }
    },

    connect_to_xero: function (frm) {
        frappe.call({
            method: "koraflow_core.doctype.xero_settings.xero_settings.authorize",
            callback: function (r) {
                if (r.message) {
                    // Open URL in new window
                    window.open(r.message, "Connect to Xero", "width=600,height=600");
                }
            }
        });
    }
});
