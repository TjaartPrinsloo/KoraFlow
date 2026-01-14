# Sales Partner Dashboard

## Overview

A custom dashboard has been created for Sales Partners to view their commission data. The dashboard includes number cards and quick links to commission reports.

## What Was Created

### Number Cards (5 Cards)

1. **Total Commission (This Month)** - Blue (#5e64ff)
   - Shows sum of `total_commission` for submitted invoices this month
   - Filtered by User Permissions (only their own sales partner)

2. **Total Commission (All Time)** - Green (#28a745)
   - Shows sum of `total_commission` for all submitted invoices
   - Filtered by User Permissions (only their own sales partner)

3. **Total Invoiced (This Month)** - Orange (#ff9800)
   - Shows sum of `base_net_total` for submitted invoices this month
   - Filtered by User Permissions (only their own sales partner)

4. **Invoices (This Month)** - Purple (#9c27b0)
   - Shows count of submitted invoices this month
   - Filtered by User Permissions (only their own sales partner)

5. **Total Invoiced (All Time)** - Cyan (#00bcd4)
   - Shows sum of `base_net_total` for all submitted invoices
   - Filtered by User Permissions (only their own sales partner)

### Workspace

**Name:** Sales Partner Dashboard (Commission Dashboard)
- **Module:** Selling
- **Icon:** chart-line
- **Public:** Yes
- **Access:** Sales Partner Portal role

**Content:**
- All 5 Number Cards displayed at the top
- Quick links to:
  - Commission Summary Report
  - Transaction Summary Report
  - My Sales Partner Record

## Security & Data Isolation

✅ **Automatic Filtering:**
- All Number Cards use User Permissions to filter data
- Each sales partner ONLY sees records where `sales_partner = themselves`
- No manual filtering needed - enforced at database level

✅ **No Sensitive Data:**
- No patient information displayed
- No item/product details shown
- Only commission and invoice totals
- No medical data accessible

## Access

Sales Partners can access the dashboard via:
- **Portal URL:** `/app/commission-dashboard` or `/app/sales-partner-dashboard`
- **Workspace:** Appears in their portal navigation

## Number Card Details

All cards:
- **Type:** Document Type (Sales Invoice)
- **Public:** Yes (accessible to all users with role)
- **Stats:** Enabled with Monthly time interval
- **Filters:** 
  - `docstatus = 1` (submitted invoices only)
  - `sales_partner IS SET` (has sales partner)
  - User Permissions automatically filter to their own partner

## Reports Available

1. **Sales Partner Commission Summary**
   - Detailed commission breakdown
   - Filtered by User Permissions

2. **Sales Partner Transaction Summary**
   - Transaction-level details
   - Filtered by User Permissions

3. **Sales Partners Commission**
   - Overall commission report
   - Filtered by User Permissions

## Technical Details

### Number Card Structure

```json
{
  "doctype": "Number Card",
  "type": "Document Type",
  "document_type": "Sales Invoice",
  "function": "Sum" or "Count",
  "aggregate_function_based_on": "total_commission" or "base_net_total",
  "filters_json": [
    ["Sales Invoice", "docstatus", "=", "1"],
    ["Sales Invoice", "sales_partner", "is", "set"]
  ]
}
```

### User Permissions

Each sales partner has a User Permission:
- **Allow:** Sales Partner
- **For Value:** Their own Sales Partner name
- **Apply To All DocTypes:** Yes

This ensures all queries automatically filter to their data only.

## Maintenance

To add new Number Cards:
1. Run `create_sales_partner_dashboard.py`
2. Add new card definition to `create_sales_partner_number_cards()`
3. Card will automatically be filtered by User Permissions

To update the workspace:
1. Edit the workspace in Frappe UI
2. Or modify `create_sales_partner_workspace()` function

## Files

- **Script:** `bench/create_sales_partner_dashboard.py`
- **Documentation:** This file

## Notes

- All cards show percentage stats (month-over-month comparison)
- Cards update automatically as new invoices are submitted
- Data is read-only - sales partners cannot modify commission data
- Workspace is public but only accessible to users with Sales Partner Portal role

