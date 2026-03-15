
import sys
import os

# Create a dummy bench environment to satisfy some frappe imports if needed, 
# but usually a simple import should work if paths are correct.
try:
    import koraflow_core
    print(f"SUCCESS: Imported koraflow_core from {koraflow_core.__file__}")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: {e}")
