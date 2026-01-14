# Healthcare Dispensing System - Quick Start Guide

## Quick Setup (5 Minutes)

### Step 1: Run Setup Script

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
bench --site koraflow-site console
```

In the console:
```python
from koraflow_core.setup_healthcare_dispensing import setup_healthcare_dispensing_system
setup_healthcare_dispensing_system()
```

**Expected Output**:
- ✅ 7 medicines created
- ✅ 7 items created and linked
- ✅ PHARM-CENTRAL-COLD warehouse created
- ✅ 3 virtual warehouses created
- ✅ 7 sales partners created
- ✅ Commission rules created
- ✅ 11 users created with roles

### Step 2: Migrate & Clear Cache

```bash
bench --site koraflow-site migrate
bench --site koraflow-site clear-cache
```

### Step 3: Verify Setup

1. **Check Medicines**: Navigate to `/app/medication`
   - Should see: Eco, Gold, Aminowell, Eco Boost, RUBY, Titanium, Ruby Boost
   - All should have Schedule = S4

2. **Check Items**: Navigate to `/app/item`
   - Should see all 7 items
   - All should have batch tracking enabled

3. **Check Warehouses**: Navigate to `/app/warehouse`
   - Should see: PHARM-CENTRAL-COLD (Physical)
   - Should see: VIRTUAL-HUB-DEL-MAS, VIRTUAL-HUB-PAARL, VIRTUAL-HUB-WORCHESTER (Virtual)

4. **Check Sales Partners**: Navigate to `/app/sales-partner`
   - Should see all 7 sales partners

5. **Check Commission Rules**: Navigate to `/app/sales-partner-commission-rule`
   - Should see commission rules for each item/partner combination

---

## Testing the Complete Workflow

### Test 1: Create Prescription → Auto Quote

1. Navigate to `/app/glp-1-patient-prescription/new`
2. Fill in:
   - Patient: Select any patient
   - Doctor: Select doctor (Andre Terblanche or Marinda Sharneck)
   - Medication: Select any S4 medication (e.g., Eco)
   - Dosage: Enter dosage
   - Quantity: Enter quantity (max 30)
   - Doctor Registration Number: Enter license number
3. Submit
4. **Expected**: 
   - Status changes to "Doctor Approved"
   - Quotation auto-created
   - Check `/app/quotation` → Should see new quotation

### Test 2: Accept Quote → Auto Sales Chain

1. Navigate to the auto-created quotation
2. Set status to "Ordered"
3. **Expected**:
   - Sales Order auto-created
   - Delivery Note auto-created
   - Sales Invoice auto-created
   - Dispense Task auto-created

### Test 3: Dispense → Stock Entry

1. Navigate to `/app/glp-1-pharmacy-dispense-task`
2. Open the task
3. Click "Populate Batch Availability"
4. Select a batch
5. Create Stock Entry:
   - Source: PHARM-CENTRAL-COLD
   - Item: Select medication item
   - Batch: Selected batch
   - Quantity: From prescription
   - **IMPORTANT**: Add patient reference (custom field)
6. Submit Stock Entry
7. **Expected**:
   - Stock Entry created
   - Dispense Confirmation auto-created

### Test 4: Commission Calculation

1. Navigate to Sales Invoice
2. Add Sales Partner to invoice
3. Submit invoice
4. **Expected**:
   - Commission calculated automatically
   - Check commission records

---

## Validation Testing

### Test Stock Entry Guard

**Try to create Stock Entry without prescription**:
1. Create Stock Entry
2. Source: PHARM-CENTRAL-COLD
3. Item: Select S4 medication
4. **Expected**: ❌ Error - "S4 medication Stock Entry must reference a prescription"

**Try to create Stock Entry from wrong warehouse**:
1. Create Stock Entry
2. Source: Any warehouse except PHARM-CENTRAL-COLD
3. Item: Select S4 medication
4. **Expected**: ❌ Error - "S4 medication can only be dispensed from PHARM-CENTRAL-COLD"

**Try to create Stock Entry without pharmacist role**:
1. Login as Doctor
2. Try to create Stock Entry
3. **Expected**: ❌ Error - "Only users with Pharmacist role can create Stock Entries"

### Test Virtual Warehouse Guard

1. Create Stock Entry
2. Source: VIRTUAL-HUB-DEL-MAS
3. **Expected**: ❌ Error - "Cannot reduce stock from virtual warehouse"

### Test Prescription Enforcement

1. Create Sales Order
2. Add S4 medication item
3. Don't link prescription
4. **Expected**: ❌ Error - "Item requires a linked prescription"

---

## Audit Replay Report

1. Navigate to Reports → Audit Replay
2. Filter by:
   - Prescription, OR
   - Patient, OR
   - Batch
3. **Expected**: Complete chain from prescription to dispense

---

## Troubleshooting

### Issue: Medicines not created
**Solution**: Check console for errors, verify Healthcare app is installed

### Issue: Commission not calculating
**Solution**: 
- Verify Sales Partner is set on invoice
- Check commission rules exist
- Check server logs for errors

### Issue: Automation not working
**Solution**:
- Clear cache: `bench --site koraflow-site clear-cache`
- Check hooks.py includes all hooks
- Check server logs

### Issue: Validations not working
**Solution**:
- Verify hooks.py updated
- Clear cache
- Check custom fields exist (prescription, patient on Stock Entry)

---

## Next Steps

1. ✅ Run setup script
2. ✅ Test complete workflow
3. ✅ Verify validations
4. ✅ Test commission calculation
5. ✅ Run audit replay report
6. ✅ Configure custom fields if needed (prescription, patient on Stock Entry)

---

**Status**: Ready for testing!
