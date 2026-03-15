
import sys
import os

try:
    import koraflow_core.koraflow_core.doctype.sales_agent.sales_agent
    print("SUCCESS: Imported sales_agent module")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: {e}")
