# Sales Partner Referral Tracking System

## Overview

A comprehensive referral tracking system for sales partners that provides:
- Safe patient data projection (no sensitive information exposed)
- Status tracking through the sales pipeline
- Commission linking
- Communication channel for questions

## Architecture

### DocTypes Created

1. **Sales Partner Referral**
   - Safe projection of patient data
   - Status tracking (Quotation Pending → Paid)
   - Links to ERP documents (hidden from portal)
   - Read-only for sales partners

2. **Sales Partner Query**
   - Commenting/question system
   - Assigned to Sales Team
   - Status tracking (Open → Responded → Closed)

### Status Mapping

| ERP Document State | Portal Status |
|-------------------|---------------|
| Quotation Draft | Quotation Pending |
| Quotation Submitted | Quotation Sent |
| Sales Order Submitted | Order Confirmed |
| Delivery Note Draft | Packing |
| Delivery Note Submitted | Dispatched |
| Sales Invoice Submitted | Invoiced |
| Payment Entry Submitted | Paid |

### Portal Pages

1. **/my-referrals** - List view with summary cards
2. **/my-referrals/<name>** - Detail view with status timeline and queries

### Security

- **Data Isolation**: User Permissions ensure sales partners only see their own referrals
- **Permission Query Conditions**: Server-side filtering by sales_partner field
- **Hidden Fields**: Patient, Quotation, Sales Order, etc. are hidden from portal users
- **No Sensitive Data**: No diagnosis, medication, financial totals, or contact details exposed

## Setup Instructions

1. **Create DocTypes** (already done):
   ```bash
   python3 create_sales_partner_referral_system.py
   ```

2. **Set up User Permissions**:
   ```bash
   python3 setup_referral_user_permissions.py
   ```

3. **Create Test Referral**:
   ```bash
   python3 create_test_referral.py
   ```

4. **Restart bench** to load hooks and routes

## Usage

### For Sales Partners

1. Log in to portal
2. Navigate to "My Referrals" (appears in portal menu)
3. View summary cards and referral list
4. Click "View" to see details
5. Click "Ask Question" to submit queries

### For Administrators

1. Create referrals when patients are referred
2. System automatically updates status as documents progress
3. Respond to queries via Sales Partner Query DocType

## Next Steps

1. Create referrals from existing sales invoices/quotations
2. Set up email notifications for query assignments
3. Add commission calculation and linking
4. Create migration script to backfill referrals from existing data

