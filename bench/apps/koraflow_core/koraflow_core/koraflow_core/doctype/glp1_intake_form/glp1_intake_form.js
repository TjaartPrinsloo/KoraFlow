// Copyright (c) 2025, KoraFlow Team and contributors
// For license information, please see license.txt

frappe.ui.form.on('GLP-1 Intake Form', {
    refresh: function (frm) {
        // Set currency to ZAR for any associated costs (User Preference)
    },

    dob: function (frm) {
        if (frm.doc.dob) {
            let birth_date = new Date(frm.doc.dob);
            let age_diff = Date.now() - birth_date.getTime();
            let age_dt = new Date(age_diff);
            let calculated_age = Math.abs(age_dt.getUTCFullYear() - 1970);
            frm.set_value('age', calculated_age);
        }
    },

    intake_weight_kg: function (frm) {
        calculate_bmi(frm);
    },

    intake_height_cm: function (frm) {
        calculate_bmi(frm);
    }
});

function calculate_bmi(frm) {
    if (frm.doc.intake_height_cm && frm.doc.intake_weight_kg) {
        // Metric Formula: weight (kg) / [height (m)]^2 [cite: 42]
        let height_m = frm.doc.intake_height_cm / 100;
        let bmi = frm.doc.intake_weight_kg / (height_m * height_m);
        frm.set_value('bmi', bmi.toFixed(1));

        // Logic for Healthy Weight & Loss Goals [cite: 47, 49, 73]
        let category = "";
        if (bmi < 18.5) category = "Underweight";
        else if (bmi < 25) category = "Normal";
        else if (bmi < 30) category = "Overweight";
        else category = "Obese";
        frm.set_value('bmi_category', category);

        // Calculate weight to reach BMI of 25 [cite: 49, 63]
        let target_weight = 25 * (height_m * height_m);
        if (frm.doc.intake_weight_kg > target_weight) {
            frm.set_value('weight_to_lose', (frm.doc.intake_weight_kg - target_weight).toFixed(1));
        } else {
            frm.set_value('weight_to_lose', 0);
        }
    }
}
