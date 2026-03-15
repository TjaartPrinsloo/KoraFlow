# Sales Agent System - Complete Implementation

## Overview

This document describes the complete Sales Agent system implementation for KoraFlow Healthcare, designed to comply with POPIA (Protection of Personal Information Act) and ensure ethical healthcare data handling.

## Core Principles

### What the Sales Agent IS
- ✅ A referrer
- ✅ A commission earner
- ✅ A status follower
- ✅ A communication bridge

### What the Sales Agent IS NOT
- ❌ Healthcare staff
- ❌ Allowed to see:
  - Medical records
  - Prescriptions
  - Diagnoses
  - Quotes
  - Pricing details
  - Contact details
  - ID numbers
  - Any POPIA-protected fields

## System Components

### 1. DocTypes

#### Patient Referral
- **Purpose**: Safe referral tracking layer between agents and patients
- **Key Fields**:
  - `referral_id`: Unique referral identifier
  - `sales_agent`: Link to User (Sales Agent)
  - `patient`: Link to Patient (restricted, hidden from agents)
  - `patient_first_name`: Frozen copy of patient name
  - `patient_last_name`: Frozen copy of patient name
  - `current_journey_status`: Status pipeline tracking
  - `sales_partner`: Link to Sales Partner for commission
  - `agent_notes`: Notes visible to agent (no patient data)
  - `internal_notes`: Notes hidden from agent

#### Commission Record
- **Purpose**: Detailed commission tracking per referral
- **Key Fields**:
  - `referral`: Link to Patient Referral
  - `sales_agent`: Link to User
  - `invoice_reference`: Masked invoice reference (INV-****1234)
  - `commission_amount`: Commission amount
  - `commission_status`: Pending/Approved/Paid
  - `expected_payout_date`: Expected payment date
  - `paid_date`: Actual payment date

#### Referral Message
- **Purpose**: Communication between agents and sales team
- **Key Fields**:
  - `referral`: Link to Patient Referral
  - `from_user`: Sender
  - `to_user`: Recipient
  - `subject`: Message subject
  - `message`: Message content
  - `status`: Unread/Read/Replied

### 2. Roles

#### Sales Agent
- **User Type**: System User
- **Desk Access**: Yes (limited)
- **Permissions**: 
  - Read-only access to own Patient Referrals
  - Read-only access to own Commission Records
  - Create/Read own Referral Messages
  - NO access to Patient, Encounter, Prescription, Sales Invoice

#### Sales Agent Manager
- **User Type**: System User
- **Desk Access**: Yes
- **Permissions**:
  - Full access to all Patient Referrals
  - Full access to Commission Records
  - Full access to Referral Messages
  - Can manage Sales Agents

### 3. Journey Status Pipeline

The status pipeline tracks patient journey without exposing medical data:

1. **Lead Received** - Initial referral received
2. **Contacted by Sales** - Sales team contacted patient
3. **Consultation Scheduled** - Appointment scheduled
4. **Consultation Completed** - Consultation finished
5. **Prescription Issued** - Prescription created (abstract, no details)
6. **Awaiting Payment** - Waiting for payment
7. **Invoice Paid** - Payment received
8. **Medication Dispatched** - Medication sent
9. **Completed** - Journey complete
10. **Cancelled** - Referral cancelled

### 4. Commission Model

- Uses ERPNext's native **Sales Partner** system
- Each Sales Agent is linked to a Sales Partner
- Commission calculated when Sales Invoice is paid
- Commission Record created automatically
- Agents see:
  - Commission amount
  - Status (Pending/Approved/Paid)
  - Expected payout date
  - Masked invoice reference
- Agents do NOT see:
  - Invoice line items
  - Product details
  - Pricing information
  - Patient contact details

### 5. Sales Agent Dashboard

The dashboard provides:

#### Section 1: Commission KPIs
- Total Commission Earned
- Pending Commission
- Paid Commission
- This Month vs Last Month comparison

#### Section 2: My Referrals
- Table view of all referrals
- Patient name (safe metadata only)
- Referral date
- Current status
- Last update
- View referral button

#### Section 3: Status Distribution
- Visual chart showing status breakdown
- Percentage distribution

#### Section 4: Recent Messages
- Latest messages to/from sales team
- Unread indicator
- Quick access to message details

### 6. Permissions Architecture

#### Permission Query Conditions
- **Patient Referral**: Agents see only their own referrals
- **Commission Record**: Agents see only their own commissions
- **Referral Message**: Users see messages they sent/received

#### Has Permission Checks
- Server-side validation
- Prevents client-side bypass
- Enforces POPIA compliance

#### Blocked DocTypes
Sales Agents are explicitly denied access to:
- Patient
- Patient Encounter
- Prescription
- Sales Invoice (direct access)
- Lab Test
- Clinical Procedure
- Any healthcare-specific DocTypes

### 7. Automation Flow

1. **Agent submits referral** (or sales captures it)
   - Patient Referral created
   - Patient name fields frozen (copied, not linked)

2. **Sales process happens internally**
   - Status updates sync to referral
   - Agent sees status changes only

3. **Sales Invoice paid**
   - Referral status → "Invoice Paid"
   - Commission Record created automatically
   - Commission calculated from invoice

4. **Agent sees updates**
   - Status change visible
   - Commission pending → paid
   - Dashboard updates automatically

### 8. API Endpoints

#### `get_dashboard_data()`
Returns comprehensive dashboard data:
- Referrals list
- Commission summary
- Recent messages
- Status distribution

#### `get_commission_summary(agent)`
Returns commission KPIs:
- Total earned
- Pending
- Paid
- This month vs last month

#### `get_agent_referrals(agent)`
Returns all referrals for an agent

#### `get_agent_commissions(agent)`
Returns all commission records for an agent

#### `create_message(referral, subject, message)`
Creates a message from agent to sales team

#### `update_referral_status(referral_id, new_status)`
Updates referral status (sales team only)

### 9. Setup Instructions

#### Initial Setup
```python
# Run after installing koraflow_core
from koraflow_core.setup_sales_agent import setup_sales_agent_system
setup_sales_agent_system()
```

Or via bench console:
```bash
bench --site your-site.localhost console
>>> from koraflow_core.setup_sales_agent import setup_sales_agent_system
>>> setup_sales_agent_system()
```

#### Creating a Sales Agent User
1. Create User with:
   - User Type: System User
   - Role: Sales Agent
   - Desk Access: Enabled

2. Link to Sales Partner:
   - Create Sales Partner record
   - Link User to Sales Partner (via custom field or email matching)

3. Set default workspace:
   - User's home page: "Sales Agent Dashboard"

### 10. Legal & POPIA Compliance

✅ **No health data exposed**
- Agents never see medical records
- Only safe metadata (name) is visible

✅ **No contact details shared**
- Patient contact info hidden
- No email, phone, address access

✅ **No prescriptions visible**
- Prescription details completely hidden
- Only abstract status shown

✅ **No financial pricing visible**
- Invoice amounts hidden
- Only commission amount shown
- Invoice references masked

✅ **Full audit trail**
- All actions logged
- Version history maintained
- Message history preserved

✅ **Principle of least privilege**
- Agents see only what they need
- Server-side permission enforcement
- No client-side security reliance

## Testing Checklist

- [ ] Sales Agent can view own referrals
- [ ] Sales Agent cannot view other agents' referrals
- [ ] Sales Agent cannot access Patient records
- [ ] Sales Agent cannot access Sales Invoice details
- [ ] Commission records created on invoice payment
- [ ] Dashboard displays correct KPIs
- [ ] Messages can be sent to sales team
- [ ] Status updates reflect correctly
- [ ] Permission query conditions work
- [ ] Has permission checks enforce restrictions

## Troubleshooting

### Agent cannot see referrals
- Check User has "Sales Agent" role
- Verify permission_query_conditions in hooks.py
- Check if_owner setting in DocType permissions

### Commission not calculating
- Verify Sales Partner linked to agent
- Check Sales Invoice has sales_partner set
- Ensure invoice status is "Paid"

### Dashboard not loading
- Check workspace exists: "Sales Agent Dashboard"
- Verify JS files included in hooks.py
- Check browser console for errors

## Support

For issues or questions, contact the KoraFlow team.

