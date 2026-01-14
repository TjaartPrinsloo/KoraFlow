# Why Number Cards Are Blank

## Issue
The Number Cards in the Sales Partner Dashboard are showing blank/empty.

## Root Cause
The Number Cards are configured correctly, but there is **no data** matching their filters:

- **Total Sales Invoices:** 7
- **Submitted Sales Invoices:** 0 ❌
- **Submitted invoices with sales_partner:** 0 ❌

## Number Card Filters
All Number Cards filter for:
1. `docstatus = 1` (submitted invoices only)
2. `sales_partner IS SET` (has a sales partner assigned)

Since there are **0 submitted invoices** with sales partners, the cards show blank.

## Solution

### Option 1: Create Test Data
Create and submit some Sales Invoices with sales partners assigned:

1. Go to **Selling > Sales Invoice > New**
2. Create an invoice
3. Set the **Sales Partner** field
4. **Submit** the invoice (docstatus = 1)
5. The Number Cards will automatically update

### Option 2: Verify Card Configuration
The cards are correctly configured:
- ✅ Type: Document Type
- ✅ Document Type: Sales Invoice  
- ✅ Function: Sum/Count
- ✅ Aggregate Field: total_commission / base_net_total
- ✅ Filters: docstatus=1, sales_partner is set
- ✅ Public: Yes

### Option 3: Test with Existing Data
If you want to test the cards immediately, you could temporarily:
1. Submit some existing invoices
2. Or modify the filters to include draft invoices (not recommended for production)

## Expected Behavior
Once there are submitted invoices with sales partners:
- Cards will show the calculated values
- Data will be automatically filtered by User Permissions
- Each sales partner will only see their own data

## Verification
To verify cards are working:
1. Create a test Sales Invoice
2. Assign a Sales Partner
3. Submit it
4. Refresh the dashboard
5. Cards should show the values

