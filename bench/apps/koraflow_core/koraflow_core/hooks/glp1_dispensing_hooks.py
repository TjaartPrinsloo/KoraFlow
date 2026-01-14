# Copyright (c) 2025, KoraFlow Team and Contributors
# License: MIT. See LICENSE

"""
GLP-1 Dispensing Hooks
Document event handlers for workflow automation
"""

import frappe
from koraflow_core.workflows.glp1_dispensing_workflow import (
	handle_intake_submission,
	handle_nurse_review_approval,
	handle_doctor_prescription_approval,
	handle_quotation_accepted,
	handle_pharmacist_dispense
)


# Document Events
doc_events = {
	"GLP-1 Intake Submission": {
		"on_submit": handle_intake_submission
	},
	"GLP-1 Intake Review": {
		"on_update": handle_nurse_review_approval
	},
	"GLP-1 Patient Prescription": {
		"on_submit": handle_doctor_prescription_approval
	},
	"Quotation": {
		"on_update_after_submit": handle_quotation_accepted
	},
	"Stock Entry": {
		"on_submit": handle_pharmacist_dispense
	}
}
