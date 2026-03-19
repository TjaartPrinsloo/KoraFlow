frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		var roles = frappe.user_roles || [];
		var isAdmin = roles.includes("System Manager") || roles.includes("Administrator");

		if (isAdmin) return;

		// Hide sections by label
		var hidden_sections = [
			"Customer PO Details",
			"Accounting Details",
			"Sales Team",
			"Print Settings",
			"Subscription",
			"Additional Info"
		];

		hidden_sections.forEach(function (label) {
			frm.fields_dict && Object.keys(frm.fields_dict).forEach(function (key) {
				var field = frm.fields_dict[key];
				if (field.df && field.df.fieldtype === "Section Break" && field.df.label === label) {
					field.wrapper && $(field.wrapper).closest(".form-section").hide();
				}
			});
		});

		// Hide sections by fieldname (but NOT sales_team_section_break — it holds sales_partner)
		var hidden_fieldnames = [
			"po_no",
			"accounting_details",
			"printing_settings",
			"subscription_section",
			"sales_team_section",
			"more_info",
		];

		hidden_fieldnames.forEach(function (fn) {
			if (frm.fields_dict[fn]) {
				$(frm.fields_dict[fn].wrapper).closest(".form-section").hide();
			}
		});

		// In the Commission section, hide the sales_team table but keep sales_partner visible
		frm.set_df_property("sales_team", "hidden", 1);
		frm.set_df_property("commission_rate", "hidden", 1);
		frm.set_df_property("total_commission", "hidden", 1);

		// Hide tabs: Connections, Terms, Payments
		setTimeout(function () {
			var hiddenTabs = ["Connections", "Terms", "Payments"];
			$(".form-tabs .nav-item .nav-link").each(function () {
				var tabLabel = $(this).text().trim();
				if (hiddenTabs.indexOf(tabLabel) !== -1) {
					$(this).parent(".nav-item").hide();
				}
			});
		}, 300);
	}
});
