frappe.ui.form.on("User", {
    refresh(frm) {
        // Only show for Administrator and only on saved docs
        if (frappe.session.user !== "Administrator" || frm.is_new()) return;
        // Don't show for Administrator's own record or Guest
        if (frm.doc.name === "Administrator" || frm.doc.name === "Guest") return;

        frm.add_custom_button(__("Change Email / Login"), function () {
            frappe.prompt(
                {
                    fieldname: "new_email",
                    label: __("New Email Address"),
                    fieldtype: "Data",
                    options: "Email",
                    reqd: 1,
                    default: frm.doc.email || frm.doc.name,
                    description: __(
                        "This will change the user's login email. All linked records (Patient, Sales Agent, etc.) will be updated automatically."
                    ),
                },
                function (values) {
                    const new_email = values.new_email.trim().toLowerCase();
                    if (new_email === frm.doc.name) {
                        frappe.msgprint(__("New email is the same as the current one."));
                        return;
                    }

                    frappe.confirm(
                        __(
                            "Change login from <b>{0}</b> to <b>{1}</b>?<br><br>This will update the user's email, login credentials, and all linked records.",
                            [frm.doc.name, new_email]
                        ),
                        function () {
                            frappe.call({
                                method: "koraflow_core.api.user_admin.change_user_email",
                                args: {
                                    old_email: frm.doc.name,
                                    new_email: new_email,
                                },
                                freeze: true,
                                freeze_message: __("Updating email and linked records..."),
                                callback: function (r) {
                                    if (r.message && r.message.success) {
                                        frappe.msgprint({
                                            title: __("Email Changed"),
                                            message: r.message.message,
                                            indicator: "green",
                                        });
                                        // Navigate to the renamed user doc
                                        frappe.set_route("Form", "User", new_email);
                                    }
                                },
                            });
                        }
                    );
                },
                __("Change User Email"),
                __("Update")
            );
        }, __("Actions"));
    },
});
