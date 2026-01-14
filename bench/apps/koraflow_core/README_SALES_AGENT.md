# Sales Agent System - Quick Start

## Overview

The Sales Agent system provides a POPIA-compliant way for sales agents to:
- Track patient referrals
- Monitor commission earnings
- Communicate with the sales team
- View referral status updates

**Without accessing any sensitive healthcare or patient data.**

## Installation

The system is automatically set up when you install `koraflow_core`. If you need to manually set it up:

```bash
bench --site your-site.localhost console
```

```python
from koraflow_core.koraflow_core.setup_sales_agent import setup_sales_agent_system
setup_sales_agent_system()
```

## Creating a Sales Agent

1. **Create User**:
   - Go to User List
   - Create new User
   - Set User Type: **System User**
   - Add Role: **Sales Agent**
   - Enable Desk Access

2. **Link to Sales Partner** (for commission tracking):
   - Create Sales Partner record
   - Set email to match User email
   - Or manually link via custom field

3. **Set Default Workspace**:
   - User's home page: `Sales Agent Dashboard`

## What Sales Agents Can See

✅ **Allowed**:
- Their own referrals (patient name only, no contact details)
- Referral status updates
- Commission amounts and status
- Messages to/from sales team
- Dashboard KPIs

❌ **Blocked**:
- Patient medical records
- Prescriptions
- Diagnoses
- Contact details (email, phone, address)
- ID numbers
- Invoice line items
- Product pricing
- Any POPIA-protected data

## Journey Status Flow

1. **Lead Received** → Agent submits referral
2. **Contacted by Sales** → Sales team contacts patient
3. **Consultation Scheduled** → Appointment made
4. **Consultation Completed** → Consultation done
5. **Prescription Issued** → Prescription created
6. **Awaiting Payment** → Waiting for payment
7. **Invoice Paid** → Payment received (commission calculated)
8. **Medication Dispatched** → Medication sent
9. **Completed** → Journey complete
10. **Cancelled** → Referral cancelled

## Commission Tracking

- Commission is calculated automatically when Sales Invoice is paid
- Commission Record is created with:
  - Commission amount
  - Status (Pending/Approved/Paid)
  - Expected payout date
  - Masked invoice reference (INV-****1234)

## Dashboard Features

The Sales Agent Dashboard shows:
- **Commission KPIs**: Total earned, pending, paid, monthly comparison
- **My Referrals**: Table of all referrals with status
- **Status Distribution**: Visual chart of status breakdown
- **Recent Messages**: Latest communications

## API Endpoints

All endpoints are whitelisted and permission-checked:

- `get_dashboard_data()` - Full dashboard data
- `get_commission_summary(agent)` - Commission KPIs
- `get_agent_referrals(agent)` - Agent's referrals
- `get_agent_commissions(agent)` - Agent's commissions
- `create_message(referral, subject, message)` - Send message
- `update_referral_status(referral_id, status)` - Update status (sales team only)

## Security

- **Server-side permissions**: All checks happen on the server
- **Query filters**: Agents only see their own data
- **Explicit denies**: Patient and healthcare DocTypes blocked
- **Audit trail**: All actions logged
- **POPIA compliant**: No sensitive data exposed

## Troubleshooting

**Agent can't see referrals?**
- Check User has "Sales Agent" role
- Verify referral's sales_agent field matches User
- Check permission_query_conditions in hooks.py

**Commission not showing?**
- Verify Sales Partner linked to agent
- Check Sales Invoice has sales_partner set
- Ensure invoice status is "Paid"
- Check Commission Record was created

**Dashboard not loading?**
- Verify workspace "Sales Agent Dashboard" exists
- Check JS files included in hooks.py
- Check browser console for errors

## Support

See `SALES_AGENT_SYSTEM.md` for complete documentation.

