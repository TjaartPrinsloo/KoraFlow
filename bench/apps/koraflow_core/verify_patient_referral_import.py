
import sys
import os

try:
    import koraflow_core.koraflow_core.doctype.patient_referral.patient_referral
    print("SUCCESS: Imported patient_referral module")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: {e}")
