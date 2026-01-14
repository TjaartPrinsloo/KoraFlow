# Sales Agent System Setup - Complete ✅

## Setup Summary

The Sales Agent system has been successfully set up on the koraflow-site.

### What Was Created

1. **Roles**
   - ✅ Sales Agent role (created)
   - ✅ Sales Agent Manager role (created)

2. **Workspace**
   - ✅ Sales Agent Dashboard workspace (created)
   - Location: `/app/workspace/Sales Agent Dashboard`
   - Contains shortcuts to:
     - My Referrals (Patient Referral list)
     - Commission Records
     - Messages (Referral Message list)

3. **Permissions**
   - ✅ Configured via DocType definitions
   - ✅ Patient access restrictions handled via hooks

### Next Steps

1. **Create Sales Agent Users**
   ```python
   # In bench console
   user = frappe.get_doc({
       "doctype": "User",
       "email": "agent@example.com",
       "first_name": "John",
       "last_name": "Doe",
       "user_type": "System User",
       "send_welcome_email": 0
   })
   user.insert()
   user.add_roles("Sales Agent")
   ```

2. **Link to Sales Partner** (for commission tracking)
   ```python
   # Create or link Sales Partner
   sales_partner = frappe.get_doc({
       "doctype": "Sales Partner",
       "partner_name": "John Doe",
       "email_id": "agent@example.com"
   })
   sales_partner.insert()
   
   # Link user to sales partner (via email matching or custom field)
   ```

3. **Set Default Workspace**
   ```python
   user = frappe.get_doc("User", "agent@example.com")
   user.default_workspace = "Sales Agent Dashboard"
   user.save()
   ```

4. **Test the System**
   - Log in as a Sales Agent user
   - Navigate to Sales Agent Dashboard
   - Create a test Patient Referral
   - Verify permissions and dashboard functionality

### Verification

To verify the setup:

```python
# Check roles exist
frappe.db.exists("Role", "Sales Agent")  # Should return True
frappe.db.exists("Role", "Sales Agent Manager")  # Should return True

# Check workspace exists
frappe.db.exists("Workspace", "Sales Agent Dashboard")  # Should return True

# Check DocTypes exist
frappe.db.exists("DocType", "Patient Referral")  # Should return True
frappe.db.exists("DocType", "Commission Record")  # Should return True
frappe.db.exists("DocType", "Referral Message")  # Should return True
```

### Files Created

- Workspace file: `bench/apps/frappe/frappe/core/workspace/sales_agent_dashboard/sales_agent_dashboard.json`
- Setup script: `bench/apps/koraflow_core/koraflow_core/setup_sales_agent.py`

### Documentation

- Complete system docs: `apps/koraflow_core/SALES_AGENT_SYSTEM.md`
- Quick start: `apps/koraflow_core/README_SALES_AGENT.md`
- Implementation summary: `apps/koraflow_core/IMPLEMENTATION_SUMMARY.md`

---

**Setup completed on:** $(date)
**Site:** koraflow-site

