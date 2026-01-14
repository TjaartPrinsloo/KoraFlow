#!/usr/bin/env python3
"""
Create Portal Page for Sales Partner Dashboard

Portal users (Website Users) can't access /app/ routes, so we need to create
a Web Page that displays the dashboard content.
"""

import sys
import os
import json

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

ROLE_NAME = "Sales Partner Portal"
PAGE_NAME = "sales-partner-dashboard"
WORKSPACE_NAME = "Commission Dashboard"


def create_portal_dashboard_page():
    """Create a Web Page for the sales partner dashboard"""
    frappe.init(site='koraflow-site')
    frappe.connect()
    
    try:
        print("=" * 80)
        print("CREATING SALES PARTNER PORTAL DASHBOARD PAGE")
        print("=" * 80)
        print()
        
        # Check if page already exists
        if frappe.db.exists("Web Page", PAGE_NAME):
            page = frappe.get_doc("Web Page", PAGE_NAME)
            print(f"  ✓ Web Page '{PAGE_NAME}' already exists, updating...")
        else:
            page = frappe.get_doc({
                "doctype": "Web Page",
                "title": "Sales Partner Dashboard",
                "route": PAGE_NAME,
                "published": 1,
                "is_standard": 0,
            })
            page.flags.ignore_permissions = True
            page.insert()
            print(f"  ✓ Created Web Page: {PAGE_NAME}")
        
        # Get workspace content
        workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
        
        # Create HTML content that loads the workspace
        # For portal users, we'll create a simple page that links to reports
        # and shows basic commission info
        
        html_content = """
<div class="sales-partner-dashboard">
    <div class="page-header">
        <h1>Commission Dashboard</h1>
        <p class="text-muted">View your commission data and reports</p>
    </div>
    
    <div class="dashboard-cards row" style="margin-top: 20px;">
        <div class="col-md-12">
            <div class="alert alert-info">
                <h4>Quick Links</h4>
                <ul>
                    <li><a href="/app/query-report/Sales Partner Commission Summary">Commission Summary Report</a></li>
                    <li><a href="/app/query-report/Sales Partner Transaction Summary">Transaction Summary Report</a></li>
                    <li><a href="/app/list/Sales Partner">My Sales Partner Record</a></li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="dashboard-info" style="margin-top: 30px;">
        <h3>Your Commission Data</h3>
        <p>All commission data is automatically filtered to show only your records.</p>
        <p>Use the links above to view detailed commission reports.</p>
    </div>
</div>

<style>
.sales-partner-dashboard {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}
.page-header {
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 15px;
    margin-bottom: 20px;
}
.dashboard-cards .alert {
    padding: 20px;
}
.dashboard-cards ul {
    margin-top: 10px;
}
.dashboard-cards li {
    margin: 10px 0;
}
.dashboard-cards a {
    font-size: 16px;
}
</style>
        """
        
        page.main_section = html_content
        
        # Set route and permissions
        page.route = PAGE_NAME
        page.published = 1
        
        # Web Page doesn't have roles field - access control is via workspace permissions
        
        page.flags.ignore_permissions = True
        page.save()
        frappe.db.commit()
        
        print(f"  ✓ Updated Web Page: {PAGE_NAME}")
        print()
        print("=" * 80)
        print("✅ PORTAL PAGE CREATED")
        print("=" * 80)
        print()
        print(f"Access URL: http://localhost:8002/{PAGE_NAME}")
        print()
        print("Note: Portal users can access this page directly.")
        print("The page includes links to commission reports.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        frappe.log_error(f"Error creating portal page: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()


if __name__ == "__main__":
    create_portal_dashboard_page()

