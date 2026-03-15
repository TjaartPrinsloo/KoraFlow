import frappe

def update_print_format():
    html_content = """
{% set patient = frappe.get_doc('Patient', doc.patient) if doc.patient else None %}

<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    @page { size: A4; margin: 0; }

    .s2w-inv {
        font-family: 'Inter', -apple-system, Arial, sans-serif;
        width: 100%;
        min-height: 1120px;
        padding: 44px 52px 56px 52px;
        color: #1e1e1e;
        position: relative;
        background: #fff;
        box-sizing: border-box;
        overflow: hidden;
    }

    /* ===== WATERMARK: Large circle arc ===== */
    .s2w-inv .wm-circle {
        position: absolute;
        top: -100px;
        left: -100px;
        width: 460px;
        height: 460px;
        border-radius: 50%;
        background: rgba(200, 200, 200, 0.12);
        z-index: 0;
        pointer-events: none;
    }

    /* ===== WATERMARK: S2W text ===== */
    .s2w-inv .wm-text {
        position: absolute;
        top: -25px;
        left: -30px;
        font-size: 290px;
        font-weight: 900;
        color: rgba(0,0,0,0.025);
        letter-spacing: -18px;
        z-index: 0;
        pointer-events: none;
        line-height: 0.85;
    }

    /* ===== DOT PATTERN ===== */
    .s2w-inv .wm-dots {
        position: absolute;
        top: 300px;
        left: 52px;
        right: 52px;
        bottom: 220px;
        background-image: radial-gradient(circle, #c5d86d40 2px, transparent 2px);
        background-size: 34px 34px;
        z-index: 0;
        pointer-events: none;
    }

    /* ===== HEADER ===== */
    .s2w-inv .inv-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        position: relative;
        z-index: 1;
        margin-bottom: 30px;
    }

    .s2w-inv .logo-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .s2w-inv .logo-icon {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: #2d3436;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 0 4px rgba(200,200,200,0.3);
    }

    .s2w-inv .logo-icon span {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -1px;
    }

    .s2w-inv .logo-icon .s-letter { color: #C1E12F; }
    .s2w-inv .logo-icon .two { color: #fff; }
    .s2w-inv .logo-icon .w-letter { color: #fff; }

    .s2w-inv .logo-text-group {
        display: flex;
        flex-direction: column;
    }

    .s2w-inv .logo-main-text {
        font-size: 30px;
        font-weight: 800;
        color: #2d3436;
        letter-spacing: -1px;
        line-height: 1;
    }

    .s2w-inv .logo-main-text .two-green {
        color: #C1E12F;
        font-weight: 900;
    }

    .s2w-inv .logo-subtitle {
        background: #C1E12F;
        color: #fff;
        font-size: 8px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 3px;
        padding: 3px 6px;
        margin-top: 3px;
        width: fit-content;
    }

    .s2w-inv .inv-title-block {
        text-align: right;
        padding-top: 8px;
    }

    .s2w-inv .inv-title {
        font-size: 34px;
        font-weight: 900;
        color: #1e1e1e;
        letter-spacing: -1px;
        margin: 0;
        line-height: 1;
    }

    .s2w-inv .inv-meta {
        font-size: 12.5px;
        color: #666;
        margin-top: 8px;
        line-height: 1.7;
    }

    /* ===== SECTION HEADERS ===== */
    .s2w-inv .section-header {
        position: relative;
        z-index: 1;
        border-top: 2.5px solid #2d3436;
        border-bottom: 1px solid #ccc;
        background: linear-gradient(180deg, #fafae8 0%, #f5f5dc 100%);
        padding: 8px 14px;
        font-weight: 800;
        font-size: 13px;
        text-transform: uppercase;
        margin: 20px 0 10px 0;
    }

    /* ===== CONTENT ROWS ===== */
    .s2w-inv .data-row {
        position: relative;
        z-index: 1;
        display: flex;
        padding: 8px 14px;
        border-bottom: 1px solid #eee;
        font-size: 13px;
    }

    .s2w-inv .data-label {
        width: 40%;
        color: #777;
        font-weight: 500;
    }

    .s2w-inv .data-value {
        width: 60%;
        font-weight: 600;
        color: #1e1e1e;
    }

    .s2w-inv .check-box {
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 1.5px solid #C1E12F;
        margin-right: 8px;
        text-align: center;
        line-height: 12px;
        font-size: 11px;
        border-radius: 2px;
        color: #C1E12F;
        font-weight: 900;
    }

    .s2w-inv .med-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        position: relative;
        z-index: 1;
    }

    .s2w-inv .med-table th {
        background: #f8f9fa;
        padding: 10px 14px;
        text-align: left;
        font-size: 12px;
        font-weight: 800;
        border-bottom: 1px solid #eee;
    }

    .s2w-inv .med-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #eee;
        font-size: 13px;
    }

    .s2w-inv .inv-footer {
        position: relative;
        z-index: 1;
        margin-top: 40px;
        padding: 20px 14px;
        border-top: 2.5px solid #2d3436;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    .s2w-inv .copyright {
        font-size: 11px;
        color: #999;
    }

    .s2w-inv .contact-col {
        text-align: right;
        font-size: 12px;
        color: #555;
    }

    .s2w-inv .accent-bar {
        position: absolute;
        bottom: 14px;
        right: 52px;
        width: 150px;
        height: 10px;
        background: linear-gradient(90deg, #d4e857, #C1E12F);
        border-radius: 5px;
    }
</style>

<div class=\"s2w-inv\">
    <!-- Watermarks -->
    <div class=\"wm-circle\"></div>
    <div class=\"wm-text\">S2W</div>
    <div class=\"wm-dots\"></div>

    <!-- Header -->
    <div class=\"inv-header\">
        <div class=\"logo-wrap\">
            <div class=\"logo-icon\">
                <span><span class=\"s-letter\">s</span><span class=\"two\">2</span><span class=\"w-letter\">w</span></span>
            </div>
            <div class=\"logo-text-group\">
                <div class=\"logo-main-text\">slim<span class=\"two-green\">2</span>well</div>
                <div class=\"logo-subtitle\">wellness simplified</div>
            </div>
        </div>
        <div class=\"inv-title-block\">
            <h1 class=\"inv-title\">INTAKE FORM</h1>
            <div class=\"inv-meta\">
                Reference: <strong>{{ doc.name }}</strong><br>
                Submission Date: <strong>{{ frappe.utils.formatdate(doc.creation) }}</strong>
            </div>
        </div>
    </div>

    <!-- Section 1 -->
    <div class=\"section-header\">1. Personal Identification</div>
    <div class=\"data-row\"><div class=\"data-label\">Full Name:</div><div class=\"data-value\">{{ doc.first_name }} {{ doc.last_name }}</div></div>
    <div class=\"data-row\"><div class=\"data-label\">Date of Birth:</div><div class=\"data-value\">{{ frappe.utils.formatdate(doc.dob) }}</div></div>
    <div class=\"data-row\"><div class=\"data-label\">Gender:</div><div class=\"data-value\">{{ doc.sex }}</div></div>
    <div class=\"data-row\"><div class=\"data-label\">Contact:</div><div class=\"data-value\">{{ doc.mobile }} / {{ doc.email }}</div></div>
    {% if doc.sa_id_number %}
        <div class=\"data-row\"><div class=\"data-label\">SA ID:</div><div class=\"data-value\">{{ doc.sa_id_number }}</div></div>
    {% elif doc.passport_number %}
        <div class=\"data-row\"><div class=\"data-label\">Passport:</div><div class=\"data-value\">{{ doc.passport_number }} ({{ doc.passport_country }})</div></div>
    {% endif %}

    <!-- Section Vitals -->
    <div class=\"section-header\">2. Vital Metrics</div>
    <div class=\"data-row\">
        <div class=\"data-label\">Height:</div>
        <div class=\"data-value\">
            {% if doc.intake_height_unit == 'Centimeters' %} {{ doc.intake_height_cm }} cm
            {% else %} {{ doc.intake_height_feet }}' {{ doc.intake_height_inches }}\" {% endif %}
        </div>
    </div>
    <div class=\"data-row\">
        <div class=\"data-label\">Weight:</div>
        <div class=\"data-value\">
            {% if doc.intake_weight_unit == 'Kilograms' %} {{ doc.intake_weight_kg }} kg
            {% else %} {{ doc.intake_weight_pounds }} lbs {% endif %}
        </div>
    </div>
    <div class=\"data-row\"><div class=\"data-label\">Blood Pressure:</div><div class=\"data-value\">{{ doc.intake_bp_systolic }}/{{ doc.intake_bp_diastolic }} mmHg</div></div>
    <div class=\"data-row\"><div class=\"data-label\">Heart Rate:</div><div class=\"data-value\">{{ doc.intake_heart_rate }} BPM</div></div>

    <!-- Section Screening -->
    <div class=\"section-header\">3. Clinical Screening & Oncology</div>
    {% set screening = [
        ('History of MTC', doc.intake_mtc),
        ('History of MEN 2', doc.intake_men2),
        ('History of Pancreatitis', doc.intake_pancreatitis),
        ('History of Gallstones', doc.intake_gallstones),
        ('Gastroparesis', doc.intake_gastroparesis),
        ('Diabetes Status', doc.intake_diabetes_type)
    ] %}
    {% for label, val in screening %}
    <div class=\"data-row\">
        <div class=\"data-label\">{{ label }}:</div>
        <div class=\"data-value\">
            {% if val in [0, 1] %}
                <span class=\"check-box\">{{ '✓' if val else ' ' }}</span> {{ 'Yes' if val else 'No' }}
            {% else %}
                {{ val }}
            {% endif %}
        </div>
    </div>
    {% endfor %}

    <!-- Section Meds -->
    <div class=\"section-header\">4. Current Medications</div>
    <div class=\"data-row\"><div class=\"data-label\">Insulin / Sulfonylureas:</div><div class=\"data-value\">{{ 'Yes' if (doc.intake_taking_insulin or doc.intake_taking_sulfonylureas) else 'No' }}</div></div>
    {% if doc.medications %}
    <table class=\"med-table\">
        <thead><tr><th>Medication</th><th>Dosage</th></tr></thead>
        <tbody>
            {% for m in doc.medications %}
            <tr><td>{{ m.medication }}</td><td>{{ m.dosage }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class=\"data-row\"><div class=\"data-value\" style=\"color: #999; font-style: italic;\">No active medications listed.</div></div>
    {% endif %}

    <!-- Section History -->
    <div class=\"section-header\">5. GLP-1 Weight Loss History</div>
    <div class=\"data-row\"><div class=\"data-label\">Previous Use:</div><div class=\"data-value\">
        {% if doc.intake_med_ozempic %} Ozempic {% endif %}
        {% if doc.intake_med_mounjaro %} Mounjaro {% endif %}
        {% if doc.intake_med_wegovy %} Wegovy {% endif %}
        {% if doc.intake_med_zepbound %} Zepbound {% endif %}
        {% if not (doc.intake_med_ozempic or doc.intake_med_mounjaro or doc.intake_med_wegovy or doc.intake_med_zepbound) %} None reported {% endif %}
    </div></div>
    {% if doc.intake_highest_dose %}
        <div class=\"data-row\"><div class=\"data-label\">Highest Dose:</div><div class=\"data-value\">{{ doc.intake_highest_dose }}</div></div>
    {% endif %}

    <!-- Section Psych -->
    <div class=\"section-header\">6. Psychological & Readiness</div>
    <div class=\"data-row\"><div class=\"data-label\">Goal Weight:</div><div class=\"data-value\">{{ doc.intake_goal_weight }} {{ 'kg' if doc.intake_weight_unit == 'Kilograms' else 'lbs' }}</div></div>
    <div class=\"data-row\"><div class=\"data-label\">SCOFF (Eating Disorders):</div><div class=\"data-value\">
        Score: {{ (doc.intake_scoff_1 or 0) + (doc.intake_scoff_2 or 0) + (doc.intake_scoff_3 or 0) + (doc.intake_scoff_4 or 0) + (doc.intake_scoff_5 or 0) }} / 5
    </div></div>

    <!-- Section Reproductive -->
    {% if doc.sex == 'Female' %}
    <div class=\"section-header\">7. Reproductive Safety</div>
    <div class=\"data-row\"><div class=\"data-label\">Pregnant / Breastfeeding:</div><div class=\"data-value\">{{ 'Yes' if (doc.intake_pregnant or doc.intake_breastfeeding) else 'No' }}</div></div>
    <div class=\"data-row\"><div class=\"data-label\">Planning to Conceive:</div><div class=\"data-value\">{{ 'Yes' if doc.intake_planning_conceive else 'No' }}</div></div>
    {% endif %}

    <!-- Footer -->
    <div class=\"inv-footer\">
        <div class=\"copyright\">
            Confidential medical document. Generated by slim 2 well clinical portal. &copy; {{ frappe.utils.now_datetime().year }}
        </div>
        <div class=\"contact-col\">
            www.slim2well.com
        </div>
    </div>

    <div class=\"accent-bar\"></div>
</div>
"""
    pf = frappe.get_doc("Print Format", "Intake Form")
    # Force it to be standard if we want it to stay in the app, but user is testing UI
    # We will save it to DB first to ensure immediate effect
    pf.html = html_content
    pf.save()
    frappe.db.commit()
    print("Updated Print Format 'Intake Form' with Premium S2W Styling")

if __name__ == "__main__":
    update_print_format()
