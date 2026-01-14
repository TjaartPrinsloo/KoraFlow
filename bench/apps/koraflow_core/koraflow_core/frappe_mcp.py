
import sys
import os
import json
from mcp.server.fastmcp import FastMCP

# Initialize Frappe Environment
# This script must be run from the bench root directory
if os.getcwd().endswith('sites'):
    os.chdir('..')

# Add 'apps' to sys.path if not present (crucial for local dev modules)
if 'apps' not in sys.path:
    sys.path.append(os.path.abspath('apps'))

try:
    import frappe
    from frappe import _
except ImportError:
    print("Error: 'frappe' module not found. Run this script from the bench environment.")
    sys.exit(1)

# Initialize FastMCP Server
mcp = FastMCP("Frappe MCP")

def init_frappe_site(site_name="koraflow-site"):
    """Initialize Frappe connection if not already active."""
    if not frappe.db:
        frappe.init(site=site_name, sites_path='sites')
        frappe.connect()

@mcp.tool()
def get_installed_apps() -> list[str]:
    """Get list of installed apps on the current site."""
    init_frappe_site()
    return frappe.get_installed_apps()

@mcp.tool()
def get_doctype_meta(doctype: str) -> dict:
    """Get metadata (fields, options) for a specific DocType."""
    init_frappe_site()
    if not frappe.db.exists("DocType", doctype):
        return {"error": f"DocType '{doctype}' not found"}
    
    meta = frappe.get_meta(doctype)
    fields = []
    for df in meta.fields:
        fields.append({
            "fieldname": df.fieldname,
            "fieldtype": df.fieldtype,
            "label": df.label,
            "reqd": df.reqd,
            "options": df.options
        })
    
    return {
        "doctype": doctype,
        "module": meta.module,
        "issingle": meta.issingle,
        "fields": fields
    }

@mcp.tool()
def get_document(doctype: str, name: str) -> dict:
    """Fetch a specific document by name."""
    init_frappe_site()
    if not frappe.db.exists(doctype, name):
        return {"error": f"Document {doctype} {name} not found"}
    
    doc = frappe.get_doc(doctype, name)
    return doc.as_dict()

@mcp.tool()
def search_docs(doctype: str, txt: str) -> list[dict]:
    """Search for documents using a text query."""
    init_frappe_site()
    return frappe.db.get_list(doctype, filters={"name": ["like", f"%{txt}%"]}, fields=["name"], limit=10)

@mcp.tool()
def ping() -> str:
    """Check if the server is running and connected to Frappe DB."""
    try:
        init_frappe_site()
        site = frappe.local.site
        return f"Pong! Connected to site: {site}"
    except Exception as e:
        return f"Error: {str(e)}"

# --- Write Capabilities ---

@mcp.tool()
def create_document(doctype: str, data: dict) -> dict:
    """Create a new document.
    
    Args:
        doctype: The DocType to create (e.g. 'ToDo', 'Note')
        data: Dictionary of field values
    """
    init_frappe_site()
    try:
        doc = frappe.get_doc({"doctype": doctype, **data})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.as_dict()
    except Exception as e:
        frappe.db.rollback()
        return {"error": str(e)}

@mcp.tool()
def update_document(doctype: str, name: str, data: dict) -> dict:
    """Update an existing document.
    
    Args:
        doctype: The DocType
        name: Name/ID of the document
        data: Dictionary of fields to update
    """
    init_frappe_site()
    try:
        doc = frappe.get_doc(doctype, name)
        doc.update(data)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.as_dict()
    except Exception as e:
        frappe.db.rollback()
        return {"error": str(e)}

@mcp.tool()
def delete_document(doctype: str, name: str) -> str:
    """Delete a document.
    
    Args:
        doctype: The DocType
        name: Name/ID of the document
    """
    init_frappe_site()
    try:
        frappe.delete_doc(doctype, name, ignore_permissions=True)
        frappe.db.commit()
        return f"Successfully deleted {doctype} {name}"
    except Exception as e:
        frappe.db.rollback()
        return f"Error deleting: {str(e)}"

# --- System Action Capabilities ---

@mcp.tool()
def run_bench_command(command: str) -> str:
    """Run a specific bench command.
    
    Allowed commands: 'migrate', 'build', 'restart', 'clear-cache'
    """
    import subprocess
    
    allowed_commands = ['migrate', 'build', 'restart', 'clear-cache']
    if command not in allowed_commands:
        return f"Error: Command '{command}' not allowed. Allowed: {allowed_commands}"
    
    try:
        # Assuming we are in bench directory
        cmd_list = ["bench", command]
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        return f"Command 'bench {command}' executed successfully.\nOutput:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error executing 'bench {command}':\n{e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
def get_error_logs(limit: int = 10) -> list[dict]:
    """Fetch recent error logs."""
    init_frappe_site()
    try:
        logs = frappe.get_all("Error Log", fields=["name", "method", "error", "creation"], order_by="creation desc", limit=limit)
        return logs
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_scheduler_status() -> dict:
    """Check status of scheduler and background jobs."""
    init_frappe_site()
    from frappe.utils.scheduler import is_scheduler_inactive
    return {
        "status": "Inactive" if is_scheduler_inactive() else "Active",
        "scheduler_enabled": not is_scheduler_inactive()
    }


if __name__ == "__main__":
    # Run MCP server over stdio for Cursor integration
    # Ensure we're in the bench directory
    script_path = os.path.abspath(__file__)
    # File is at: bench/apps/koraflow_core/koraflow_core/frappe_mcp.py
    # Need to go up 4 levels to get to bench directory
    bench_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path))))
    
    # Verify we found the bench directory
    if not os.path.exists(os.path.join(bench_dir, 'sites')):
        # If not found, try to find it by looking for sites directory
        current = os.path.dirname(script_path)
        while current != os.path.dirname(current):  # Not at root
            if os.path.exists(os.path.join(current, 'sites')):
                bench_dir = current
                break
            current = os.path.dirname(current)
    
    # Change to bench directory
    os.chdir(bench_dir)
    
    # Run MCP server with stdio transport
    mcp.run(transport="stdio")
