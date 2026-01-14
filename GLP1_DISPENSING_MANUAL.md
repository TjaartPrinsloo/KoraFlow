# GLP-1 Dispensing Structure - Complete Testing & User Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [DocTypes Reference](#doctypes-reference)
4. [Complete Workflow Guide](#complete-workflow-guide)
5. [Compliance Checkpoints](#compliance-checkpoints)
6. [Role-Based Permissions](#role-based-permissions)
7. [Step-by-Step Testing Procedures](#step-by-step-testing-procedures)
8. [Expected Behaviors](#expected-behaviors)
9. [Troubleshooting](#troubleshooting)
10. [API Endpoints](#api-endpoints)

---

## System Overview

### Purpose
The GLP-1 Dispensing Structure is a SAHPRA-compliant system for managing the complete lifecycle of GLP-1 medication dispensing, from patient intake through final dispense, with strict compliance controls, audit trails, and role-based access.

### Key Features
- **11 Custom DocTypes** for GLP-1 specific workflows
- **6 Compliance Checkpoints** (CP-A through CP-F) enforcing regulatory requirements
- **State Machine Workflow** with automated transitions and human gates
- **Immutable Audit Trail** for all critical actions
- **Cold Chain Management** with temperature monitoring
- **Batch Traceability** for complete medication tracking
- **Role-Based Access Control** with strict separation of duties

---

## Architecture & Design Principles

### Physical vs. Virtual Warehouses
- **Physical Warehouse**: `PHARM-CENTRAL-COLD` - Single licensed pharmacy warehouse (2-8°C)
- **Virtual Warehouses**: Multiple operational warehouses for allocation tracking (no physical stock)

### Automation Boundaries
- **Automated**: Quote generation, sales chain creation, allocation creation
- **Human Gates**: Nurse review, doctor approval, pharmacist dispense, patient acknowledgment

### Compliance Principles
1. **Prescription Immutability**: Once approved, critical fields cannot be changed
2. **Batch Traceability**: Every batch must be traceable in <30 seconds
3. **Cold Chain Enforcement**: Temperature excursions block dispensing
4. **Role Isolation**: Doctors cannot see stock, Sales cannot see prescriptions
5. **Anti-Wholesaling**: Every dispense must reference a specific patient
6. **Audit Mode**: Complete audit trail for SAHPRA compliance

---

## DocTypes Reference

### 1. Pharmacy Warehouse
**Purpose**: Manages physical and virtual warehouses for GLP-1 dispensing

**Key Fields**:
- `warehouse_name`: Name of the warehouse
- `warehouse_type`: Physical or Virtual
- `is_licensed`: Whether the warehouse has a pharmacy license
- `pharmacy_license_number`: License number (required for physical)
- `cold_chain_enabled`: Whether cold chain monitoring is active
- `erpnext_warehouse`: Link to ERPNext's standard Warehouse

**Validations**:
- Physical warehouses must have a license number
- `erpnext_warehouse` must exist

**Testing**:
1. Navigate to `/app/pharmacy-warehouse/new`
2. Create a physical warehouse:
   - Name: `PHARM-CENTRAL-COLD`
   - Type: `Physical`
   - License: `PH-12345`
   - Cold Chain: ✅ Enabled
   - Link to ERPNext Warehouse
3. Create virtual warehouses:
   - Name: `CLINIC-A-VIRTUAL`
   - Type: `Virtual`
   - No license required

**Expected**: Physical warehouse requires license, virtual does not.

---

### 2. GLP-1 Patient Prescription
**Purpose**: Records doctor-approved GLP-1 prescriptions

**Key Fields**:
- `patient`: Link to Patient
- `doctor`: Link to Healthcare Practitioner
- `medication`: Link to Medication
- `dosage`: Prescribed dosage
- `quantity`: Quantity (max 30 days)
- `status`: Draft → Doctor Approved → Dispensed → Closed
- `doctor_registration_number`: Doctor's license number

**Validations**:
- Doctor registration number required
- Medication must be Schedule 4 (S4)
- Quantity cannot exceed 30 days
- Cannot modify after approval (immutable fields)

**Status Flow**:
1. **Draft**: Prescription created, not yet approved
2. **Doctor Approved**: Doctor has approved (auto on submit)
3. **Dispensed**: Medication has been dispensed
4. **Closed**: Prescription completed

**Testing**:
1. Create new prescription:
   - Patient: Select existing patient
   - Doctor: Select healthcare practitioner
   - Medication: Select GLP-1 medication (must be S4)
   - Dosage: Enter dosage
   - Quantity: Enter quantity (max 30)
   - Doctor Registration: Enter license number
2. Save as Draft
3. Submit → Status should change to "Doctor Approved"
4. Try editing patient/medication/dosage → Should be blocked
5. Check audit log → Should see entry created

**Expected**:
- Cannot submit without doctor registration number
- Cannot exceed 30 days quantity
- Status auto-changes to "Doctor Approved" on submit
- Immutable fields blocked after approval
- Audit log entry created

---

### 3. GLP-1 Intake Review
**Purpose**: Nurse review of patient intake submissions

**Key Fields**:
- `intake_submission`: Link to GLP-1 Intake Submission
- `reviewer`: Link to User (must have Nurse role)
- `status`: Pending → Approved/Declined/Needs More Info
- `review_notes`: Nurse's review notes
- `suggested_prescription`: Link to Draft prescription (optional)

**Validations**:
- Reviewer must have "Nurse" role
- Suggested prescription must be in Draft status

**Workflow**:
1. Auto-created when intake submission is submitted
2. Nurse reviews and sets status
3. If approved, nurse can suggest a prescription (draft only)

**Testing**:
1. Submit a GLP-1 Intake Submission
2. Check → GLP-1 Intake Review should be auto-created
3. Open the review
4. Set reviewer (must be user with Nurse role)
5. Review intake data
6. Set status to "Approved"
7. Optionally link a draft prescription
8. Save

**Expected**:
- Review auto-created on intake submission
- Cannot set reviewer without Nurse role
- Can only link Draft prescriptions
- Status changes trigger workflow

---

### 4. GLP-1 Dispense Request
**Purpose**: Signal from doctor to pharmacy for dispense (NOT stock movement)

**Key Fields**:
- `prescription`: Link to GLP-1 Patient Prescription (must be Doctor Approved)
- `requested_quantity`: Quantity to dispense
- `preferred_clinic`: Link to Virtual Warehouse
- `urgency`: Normal/Urgent
- `status`: Draft → Submitted

**Validations**:
- Prescription must be "Doctor Approved"
- Cannot exceed prescription quantity

**Testing**:
1. Create dispense request:
   - Prescription: Select approved prescription
   - Quantity: Enter quantity (≤ prescription quantity)
   - Preferred Clinic: Select virtual warehouse
   - Urgency: Select level
2. Submit

**Expected**:
- Cannot create for non-approved prescriptions
- Quantity validation works
- Triggers pharmacy review workflow

---

### 5. GLP-1 Pharmacy Review
**Purpose**: Pharmacist validation checkpoint before dispense

**Key Fields**:
- `dispense_request`: Link to GLP-1 Dispense Request
- `pharmacist`: Link to User (must have Pharmacist role)
- `pharmacist_license_number`: Pharmacist's license
- `review_status`: Pending → Approved/Rejected/Needs Clarification
- `patient_history_reviewed`: Checkbox
- `dosing_appropriate`: Checkbox
- `validation_notes`: Notes

**Validations**:
- Pharmacist must have "Pharmacist" role
- License number required
- Creates audit log on approval

**Testing**:
1. Create pharmacy review:
   - Dispense Request: Select submitted request
   - Pharmacist: Select user with Pharmacist role
   - License: Enter license number
   - Review Status: Set to "Approved"
   - Check: Patient History Reviewed
   - Check: Dosing Appropriate
2. Submit

**Expected**:
- Cannot set pharmacist without Pharmacist role
- License number required
- Audit log created on approval
- Triggers allocation creation

---

### 6. GLP-1 Compounding Record
**Purpose**: Tracks compounding activities (if medication is compounded)

**Key Fields**:
- `prescription`: Link to prescription
- `patient`: Link to patient
- `source_batch`: Source batch for compounding
- `compound_quantity`: Quantity compounded
- `beyond_use_date`: BUD (max 30 days from compound date)
- `responsible_pharmacist`: Pharmacist who compounded
- `pharmacist_license`: License number

**Validations**:
- Quantity cannot exceed 30 days
- Cannot exceed prescription quantity
- Prescription and patient must match
- Creates audit log on submit

**Testing**:
1. Create compounding record:
   - Prescription: Select prescription
   - Patient: Select patient (must match prescription)
   - Source Batch: Select batch
   - Compound Quantity: Enter (max 30 days)
   - Beyond Use Date: Set (max 30 days from today)
   - Responsible Pharmacist: Select pharmacist
   - License: Enter license
2. Submit

**Expected**:
- Patient must match prescription
- Quantity limits enforced
- BUD cannot exceed 30 days
- Audit log created

---

### 7. GLP-1 Dispense Allocation
**Purpose**: Virtual allocation of stock (logical reservation, not physical movement)

**Key Fields**:
- `prescription`: Link to prescription
- `patient`: Link to patient
- `allocated_quantity`: Quantity allocated
- `virtual_warehouse`: Virtual warehouse (NOT physical)
- `status`: Reserved → Released → Cancelled

**Validations**:
- Can only use virtual warehouses
- No physical stock movement

**Testing**:
1. Create allocation:
   - Prescription: Select prescription
   - Patient: Select patient
   - Allocated Quantity: Enter quantity
   - Virtual Warehouse: Select virtual warehouse (NOT PHARM-CENTRAL-COLD)
2. Submit

**Expected**:
- Cannot use physical warehouse
- No stock entry created
- Logical reservation only

---

### 8. GLP-1 Pharmacy Dispense Task
**Purpose**: Queue item for pharmacists to action dispenses

**Key Fields**:
- `patient`: Link to patient
- `prescription`: Link to prescription
- `allocation`: Link to allocation
- `invoice`: Link to Sales Invoice
- `batch_availability`: Child table with available batches
- `status`: Pending → In Progress → Completed

**Key Functions**:
- `populate_batch_availability()`: Fills child table with available batches from PHARM-CENTRAL-COLD

**Testing**:
1. Create dispense task (usually auto-created from allocation):
   - Patient: Select patient
   - Prescription: Select prescription
   - Allocation: Select allocation
   - Invoice: Select invoice
2. Click "Populate Batch Availability"
3. Check child table → Should show available batches

**Expected**:
- Batch availability populated from PHARM-CENTRAL-COLD
- Shows expiry dates and available quantities
- Pharmacist can select batch for dispense

---

### 9. GLP-1 Dispense Confirmation
**Purpose**: Final patient handover record

**Key Fields**:
- `prescription`: Link to prescription
- `patient`: Link to patient
- `stock_entry`: Link to Stock Entry (required)
- `batch`: Batch dispensed
- `pharmacist`: Dispensing pharmacist
- `patient_acknowledgment`: Checkbox (required)
- `counseling_record`: Notes on patient counseling

**Validations**:
- Patient acknowledgment required
- Stock Entry must be submitted
- Updates prescription status to "Dispensed"
- Creates audit log

**Testing**:
1. Create dispense confirmation:
   - Prescription: Select prescription
   - Patient: Select patient
   - Stock Entry: Select submitted stock entry
   - Batch: Select batch
   - Pharmacist: Select pharmacist
   - Check: Patient Acknowledgment
   - Counseling: Enter notes
2. Submit

**Expected**:
- Cannot submit without patient acknowledgment
- Stock Entry must be submitted
- Prescription status updates to "Dispensed"
- Audit log created

---

### 10. GLP-1 Compliance Audit Log
**Purpose**: Immutable log for critical compliance events

**Key Fields**:
- `event_type`: Type of event (Prescription, Dispense, Compounding, etc.)
- `reference_doctype`: Related DocType
- `reference_name`: Related document name
- `patient`: Patient involved
- `actor`: User who performed action
- `actor_license`: License number
- `timestamp`: When event occurred
- `details`: JSON details

**Validations**:
- Cannot be modified after creation
- Cannot be deleted
- Timestamp auto-set

**Testing**:
1. Perform any critical action (prescription approval, dispense, etc.)
2. Check audit log → Should see entry
3. Try to edit → Should be blocked
4. Try to delete → Should be blocked

**Expected**:
- Entries created automatically
- Immutable (cannot edit/delete)
- Complete audit trail

---

### 11. GLP-1 Cold Chain Log
**Purpose**: Records temperature and handling checks

**Key Fields**:
- `batch`: Batch being monitored
- `warehouse`: Warehouse location
- `temperature`: Temperature reading
- `check_time`: When checked
- `checked_by`: User who checked
- `excursion`: Auto-flagged if outside 2-8°C
- `excursion_resolved`: Whether resolved

**Validations**:
- Auto-flags excursions (outside 2-8°C)
- Blocks dispensing if unresolved excursion

**Testing**:
1. Create cold chain log:
   - Batch: Select batch
   - Warehouse: Select warehouse
   - Temperature: Enter temperature
   - Check Time: Set time
   - Checked By: Select user
2. If temperature < 2°C or > 8°C → Excursion auto-flagged
3. Try to dispense batch with unresolved excursion → Should be blocked

**Expected**:
- Excursions auto-detected
- Dispensing blocked if excursion unresolved
- Temperature history maintained

---

### 12. GLP-1 Batch Availability (Child Table)
**Purpose**: Lists available batches for dispense tasks

**Key Fields**:
- `batch`: Batch number
- `expiry_date`: Expiry date
- `available_quantity`: Available quantity

**Usage**: Populated automatically in GLP-1 Pharmacy Dispense Task

---

## Complete Workflow Guide

### End-to-End Workflow: Intake to Dispense

#### Step 1: Patient Intake Submission
**Actor**: Patient (via web form)

1. Patient fills out GLP-1 Intake Form
2. Patient submits GLP-1 Intake Submission
3. **AUTOMATED**: System creates GLP-1 Intake Review

**Expected**:
- Intake Review auto-created with status "Pending"
- Review linked to intake submission

---

#### Step 2: Nurse Review (Human Gate #1)
**Actor**: Nurse

1. Nurse opens GLP-1 Intake Review
2. Nurse reviews patient data:
   - Checks contraindications
   - Reviews medical history
   - Validates vitals
3. Nurse sets status:
   - **Approved**: Patient suitable for GLP-1
   - **Declined**: Patient not suitable
   - **Needs More Info**: Requires additional information
4. Nurse adds review notes
5. (Optional) Nurse creates Draft prescription suggestion

**Expected**:
- Only users with "Nurse" role can review
- Status change triggers workflow
- Draft prescription can be linked if approved

---

#### Step 3: Doctor Prescription Creation
**Actor**: Doctor

1. Doctor creates GLP-1 Patient Prescription:
   - Links to patient
   - Selects medication (must be S4)
   - Sets dosage and quantity (max 30 days)
   - Enters doctor registration number
2. Doctor saves as Draft
3. Doctor reviews prescription
4. Doctor submits → **AUTOMATED**: Status changes to "Doctor Approved"

**Expected**:
- Prescription cannot exceed 30 days
- Doctor registration number required
- Status auto-changes on submit
- Audit log entry created
- Quote auto-generated (Step 4)

---

#### Step 4: Quote Generation (Automated)
**Actor**: System

1. **AUTOMATED**: System creates Quotation from prescription
2. Quotation includes:
   - Patient's customer record
   - Medication item
   - Quantity from prescription
   - Standard rate
3. Quotation is submitted automatically

**Expected**:
- Quote created automatically
- Linked to prescription
- Ready for patient acceptance

---

#### Step 5: Patient Accepts Quote (Human Gate #2)
**Actor**: Patient/Sales

1. Patient reviews quotation
2. Patient accepts quote → Status changes to "Ordered"
3. **AUTOMATED**: System creates sales chain (Step 6)

**Expected**:
- Quote status changes to "Ordered"
- Triggers sales chain creation

---

#### Step 6: Sales Chain Creation (Automated)
**Actor**: System

1. **AUTOMATED**: System creates Sales Order from quotation
2. **AUTOMATED**: System creates Delivery Note from Sales Order
3. **AUTOMATED**: System creates Sales Invoice from Delivery Note
4. **AUTOMATED**: System creates GLP-1 Dispense Allocation (Step 7)

**Expected**:
- Sales Order created
- Delivery Note created
- Sales Invoice created
- All linked to prescription

---

#### Step 7: Dispense Allocation (Automated)
**Actor**: System

1. **AUTOMATED**: System creates GLP-1 Dispense Allocation
2. Allocation:
   - Links to prescription and patient
   - Uses virtual warehouse (NOT physical)
   - Sets quantity from invoice
   - Status: "Reserved"
3. **AUTOMATED**: System creates GLP-1 Pharmacy Dispense Task (Step 8)

**Expected**:
- Allocation uses virtual warehouse only
- No physical stock movement
- Dispense task created

---

#### Step 8: Pharmacist Dispense Task
**Actor**: Pharmacist

1. Pharmacist opens GLP-1 Pharmacy Dispense Task
2. Pharmacist clicks "Populate Batch Availability"
3. System shows available batches from PHARM-CENTRAL-COLD:
   - Batch numbers
   - Expiry dates
   - Available quantities
4. Pharmacist selects batch
5. Pharmacist creates Stock Entry:
   - Source: PHARM-CENTRAL-COLD
   - Destination: Patient (or clinic virtual warehouse)
   - Batch: Selected batch
   - Quantity: From allocation
   - **CRITICAL**: Must include patient reference
6. Pharmacist submits Stock Entry → **AUTOMATED**: Triggers Step 9

**Expected**:
- Batch availability populated
- Stock Entry must reference patient
- Source must be PHARM-CENTRAL-COLD
- Cold chain validation occurs
- Triggers dispense confirmation

---

#### Step 9: Dispense Confirmation (Human Gate #3)
**Actor**: Pharmacist

1. **AUTOMATED**: System creates GLP-1 Dispense Confirmation
2. Pharmacist completes confirmation:
   - Links to Stock Entry
   - Selects batch
   - Enters pharmacist name
   - **REQUIRED**: Checks "Patient Acknowledgment"
   - Enters counseling notes
3. Pharmacist submits confirmation

**Expected**:
- Patient acknowledgment required
- Stock Entry must be submitted
- Prescription status updates to "Dispensed"
- Audit log entry created
- Workflow complete

---

## Compliance Checkpoints

### CP-A: Prescription Lock
**Purpose**: Prevent modification of prescriptions after dispensing

**Implementation**:
- Prescription fields are immutable after "Doctor Approved" status
- Cannot edit: patient, medication, dosage, quantity, doctor
- System checks on update

**Testing**:
1. Create and approve prescription
2. Try to edit patient → Should be blocked
3. Try to edit medication → Should be blocked
4. Try to edit dosage → Should be blocked
5. Dispense medication
6. Try to edit again → Should still be blocked

**Expected**: All edits blocked after approval

---

### CP-B: Batch Traceability
**Purpose**: Complete batch traceability in <30 seconds

**Implementation**:
- `get_batch_traceability()` function queries all related records
- Returns: compounding records, dispenses, stock movements, cold chain logs

**Testing**:
1. Create batch
2. Use batch in compounding → Record created
3. Use batch in dispense → Record created
4. Create cold chain log → Record created
5. Call traceability function → Should return all records in <30 seconds

**Expected**: Complete traceability returned quickly

---

### CP-C: Cold Chain Enforcement
**Purpose**: Block dispensing if cold chain compromised

**Implementation**:
- Temperature logs checked before dispense
- Excursions (outside 2-8°C) flagged automatically
- Dispensing blocked if unresolved excursion

**Testing**:
1. Create batch
2. Create cold chain log with temperature 10°C → Excursion flagged
3. Try to create Stock Entry with this batch → Should be blocked
4. Resolve excursion (set `excursion_resolved` = 1)
5. Try Stock Entry again → Should be allowed

**Expected**: Dispensing blocked with unresolved excursions

---

### CP-D: Role Isolation
**Purpose**: Strict separation of duties

**Implementation**:
- Doctors: Can see prescriptions, cannot see stock
- Pharmacists: Can see stock and dispenses, cannot see sales data
- Sales: Can see sales data, cannot see prescriptions
- Compliance Officer: Read-only access to audit logs

**Testing**:
1. Login as Doctor:
   - Should see: Prescriptions, Intake Reviews
   - Should NOT see: Stock Entries, Warehouses, Dispense Tasks
2. Login as Pharmacist:
   - Should see: Dispense Tasks, Stock Entries, Warehouses
   - Should NOT see: Sales Orders, Quotations
3. Login as Sales:
   - Should see: Quotations, Sales Orders, Invoices
   - Should NOT see: Prescriptions, Dispense Tasks
4. Login as Compliance Officer:
   - Should see: Audit Logs (read-only)
   - Should NOT see: Ability to edit/delete

**Expected**: Role-based access enforced

---

### CP-E: Anti-Wholesaling Guard
**Purpose**: Every dispense must reference a specific patient

**Implementation**:
- Stock Entry validation checks for patient reference
- Cannot create Stock Entry from PHARM-CENTRAL-COLD without patient
- Patient must match prescription

**Testing**:
1. Try to create Stock Entry:
   - Source: PHARM-CENTRAL-COLD
   - No patient reference → Should be blocked
2. Create Stock Entry with patient reference → Should be allowed
3. Try to create Stock Entry with wrong patient → Should be blocked

**Expected**: Patient reference required and validated

---

### CP-F: SAHPRA Audit Mode
**Purpose**: Complete audit trail for regulatory compliance

**Implementation**:
- Audit log entries for all critical actions
- Immutable audit records
- SAHPRA audit report available

**Testing**:
1. Perform critical actions:
   - Approve prescription → Check audit log
   - Dispense medication → Check audit log
   - Compound medication → Check audit log
2. Try to edit audit log → Should be blocked
3. Try to delete audit log → Should be blocked
4. Generate SAHPRA audit report → Should show all activities

**Expected**: Complete, immutable audit trail

---

## Role-Based Permissions

### Doctor (Healthcare Practitioner)
**Can**:
- Create and edit GLP-1 Patient Prescriptions (Draft only)
- View GLP-1 Intake Reviews
- View own prescriptions
- Approve prescriptions (submit)

**Cannot**:
- View stock levels
- View warehouses
- Create Stock Entries
- View dispense tasks
- Edit prescriptions after approval

**Testing**:
1. Login as Doctor
2. Navigate to GLP-1 Patient Prescription → Should see list
3. Create new prescription → Should work
4. Navigate to Stock Entry → Should NOT see or be blocked
5. Navigate to Warehouse → Should NOT see

---

### Nurse
**Can**:
- View GLP-1 Intake Submissions
- Create and edit GLP-1 Intake Reviews
- Suggest draft prescriptions
- View intake reviews

**Cannot**:
- Approve prescriptions
- View stock
- Create dispense tasks

**Testing**:
1. Login as Nurse
2. Navigate to GLP-1 Intake Review → Should see list
3. Create review → Should work
4. Navigate to GLP-1 Patient Prescription → Should see but not create
5. Navigate to Stock Entry → Should NOT see

---

### Pharmacist
**Can**:
- View GLP-1 Pharmacy Dispense Tasks
- Create Stock Entries (with patient reference)
- Create GLP-1 Dispense Confirmations
- View batches and warehouses
- Create GLP-1 Compounding Records
- Create GLP-1 Cold Chain Logs
- Create GLP-1 Pharmacy Reviews

**Cannot**:
- View prescriptions (except through dispense tasks)
- View sales data
- Edit prescriptions

**Testing**:
1. Login as Pharmacist
2. Navigate to GLP-1 Pharmacy Dispense Task → Should see list
3. Create Stock Entry → Should work (with patient)
4. Navigate to GLP-1 Patient Prescription → Should NOT see full list
5. Navigate to Sales Order → Should NOT see

---

### Sales
**Can**:
- View Quotations
- View Sales Orders
- View Invoices
- Accept quotations

**Cannot**:
- View prescriptions
- View dispense tasks
- View stock
- View intake reviews

**Testing**:
1. Login as Sales
2. Navigate to Quotation → Should see list
3. Navigate to GLP-1 Patient Prescription → Should NOT see
4. Navigate to Stock Entry → Should NOT see

---

### Compliance Officer
**Can**:
- View GLP-1 Compliance Audit Log (read-only)
- Generate SAHPRA audit reports
- View batch traceability reports

**Cannot**:
- Edit any documents
- Delete any documents
- Create any documents

**Testing**:
1. Login as Compliance Officer
2. Navigate to GLP-1 Compliance Audit Log → Should see list (read-only)
3. Try to edit → Should be blocked
4. Generate reports → Should work

---

## Step-by-Step Testing Procedures

### Test 1: Complete End-to-End Workflow

#### Prerequisites
1. Create test patient
2. Create test doctor (Healthcare Practitioner)
3. Create test pharmacist (User with Pharmacist role)
4. Create GLP-1 medication (Schedule 4)
5. Create PHARM-CENTRAL-COLD warehouse
6. Create virtual warehouse

#### Steps

**1. Patient Intake**
```
1. Navigate to GLP-1 Intake Submission
2. Create new submission
3. Fill in patient data
4. Submit
5. Verify: GLP-1 Intake Review auto-created
```

**2. Nurse Review**
```
1. Navigate to GLP-1 Intake Review
2. Open auto-created review
3. Set reviewer (Nurse user)
4. Review data
5. Set status to "Approved"
6. Save
7. Verify: Status is "Approved"
```

**3. Doctor Prescription**
```
1. Navigate to GLP-1 Patient Prescription
2. Create new prescription
3. Select patient
4. Select doctor
5. Select medication (S4)
6. Enter dosage and quantity (max 30)
7. Enter doctor registration number
8. Save as Draft
9. Submit
10. Verify: Status changes to "Doctor Approved"
11. Verify: Audit log entry created
12. Verify: Quotation auto-created
```

**4. Patient Accepts Quote**
```
1. Navigate to Quotation
2. Open auto-created quotation
3. Accept quote (set status to "Ordered")
4. Verify: Sales Order created
5. Verify: Delivery Note created
6. Verify: Sales Invoice created
7. Verify: GLP-1 Dispense Allocation created
8. Verify: GLP-1 Pharmacy Dispense Task created
```

**5. Pharmacist Dispense**
```
1. Navigate to GLP-1 Pharmacy Dispense Task
2. Open task
3. Click "Populate Batch Availability"
4. Verify: Batches shown from PHARM-CENTRAL-COLD
5. Select batch
6. Create Stock Entry:
   - Source: PHARM-CENTRAL-COLD
   - Destination: Patient or virtual warehouse
   - Batch: Selected batch
   - Quantity: From allocation
   - Patient: Select patient
7. Submit Stock Entry
8. Verify: GLP-1 Dispense Confirmation auto-created
```

**6. Dispense Confirmation**
```
1. Navigate to GLP-1 Dispense Confirmation
2. Open auto-created confirmation
3. Verify: Stock Entry linked
4. Verify: Batch selected
5. Check "Patient Acknowledgment"
6. Enter counseling notes
7. Submit
8. Verify: Prescription status = "Dispensed"
9. Verify: Audit log entry created
```

**Expected Results**:
- All steps complete successfully
- All automated transitions occur
- All audit logs created
- Prescription status updates correctly
- No errors in workflow

---

### Test 2: Compliance Checkpoint Testing

#### CP-A: Prescription Lock
```
1. Create and approve prescription
2. Try to edit patient → Should fail
3. Try to edit medication → Should fail
4. Try to edit dosage → Should fail
5. Dispense medication
6. Try to edit again → Should still fail
```

#### CP-B: Batch Traceability
```
1. Create batch
2. Use in compounding → Create compounding record
3. Use in dispense → Create dispense confirmation
4. Create cold chain log
5. Call traceability function
6. Verify: All records returned in <30 seconds
```

#### CP-C: Cold Chain Enforcement
```
1. Create batch
2. Create cold chain log with temperature 10°C
3. Verify: Excursion flagged
4. Try to create Stock Entry → Should fail
5. Resolve excursion
6. Try Stock Entry again → Should succeed
```

#### CP-D: Role Isolation
```
1. Login as Doctor → Verify access
2. Login as Pharmacist → Verify access
3. Login as Sales → Verify access
4. Login as Compliance Officer → Verify access
```

#### CP-E: Anti-Wholesaling
```
1. Try Stock Entry without patient → Should fail
2. Create Stock Entry with patient → Should succeed
3. Try with wrong patient → Should fail
```

#### CP-F: Audit Trail
```
1. Perform critical actions
2. Check audit logs → Should see entries
3. Try to edit audit log → Should fail
4. Try to delete audit log → Should fail
```

---

### Test 3: Validation Testing

#### Prescription Validations
```
1. Try to create prescription without doctor registration → Should fail
2. Try quantity > 30 days → Should fail
3. Try non-S4 medication → Should fail
4. Create valid prescription → Should succeed
```

#### Compounding Validations
```
1. Try quantity > 30 days → Should fail
2. Try quantity > prescription quantity → Should fail
3. Try patient mismatch → Should fail
4. Create valid compounding record → Should succeed
```

#### Stock Entry Validations
```
1. Try source ≠ PHARM-CENTRAL-COLD → Should fail
2. Try without patient → Should fail
3. Try with cold chain excursion → Should fail
4. Create valid Stock Entry → Should succeed
```

---

### Test 4: Workflow Automation Testing

#### Automated Transitions
```
1. Submit intake → Verify review created
2. Approve prescription → Verify quote created
3. Accept quote → Verify sales chain created
4. Submit Stock Entry → Verify dispense confirmation created
```

#### Human Gates
```
1. Nurse review → Must be manual
2. Doctor approval → Must be manual
3. Patient quote acceptance → Must be manual
4. Pharmacist dispense → Must be manual
5. Patient acknowledgment → Must be manual
```

---

## Expected Behaviors

### Normal Flow Behaviors

1. **Intake Submission**:
   - Creates Intake Review automatically
   - Review status: "Pending"
   - Linked to submission

2. **Prescription Approval**:
   - Status changes to "Doctor Approved" on submit
   - Audit log entry created
   - Quotation auto-generated
   - Immutable fields locked

3. **Quote Acceptance**:
   - Sales chain auto-created (Order → Delivery → Invoice)
   - Dispense allocation auto-created
   - Dispense task auto-created

4. **Stock Entry Submission**:
   - Validates patient reference
   - Validates cold chain
   - Validates source warehouse
   - Creates dispense confirmation

5. **Dispense Confirmation**:
   - Updates prescription status to "Dispensed"
   - Creates audit log entry
   - Requires patient acknowledgment

### Error Behaviors

1. **Validation Errors**:
   - Clear error messages
   - Field-level validation
   - Prevents invalid data entry

2. **Permission Errors**:
   - Access denied messages
   - Role-based restrictions enforced
   - Cannot bypass permissions

3. **Workflow Errors**:
   - Prevents invalid state transitions
   - Requires prerequisites
   - Maintains data integrity

---

## Troubleshooting

### Issue: DocType Not Found
**Symptoms**: "Page not found" error when accessing DocType

**Solutions**:
1. Run migration: `bench --site koraflow-site migrate`
2. Clear cache: `bench --site koraflow-site clear-cache`
3. Reload DocType: `bench --site koraflow-site reload-doc koraflow_core doctype glp_1_patient_prescription`

---

### Issue: Workflow Not Triggering
**Symptoms**: Automated steps not executing

**Solutions**:
1. Check hooks.py includes workflow functions
2. Verify DocType has correct hooks
3. Check server logs for errors
4. Verify document status is correct

---

### Issue: Permission Denied
**Symptoms**: Cannot access DocType or perform action

**Solutions**:
1. Check user role assignments
2. Verify role permissions in DocType
3. Check permission query conditions
4. Verify has_permission functions

---

### Issue: Validation Failing
**Symptoms**: Cannot save document due to validation

**Solutions**:
1. Check required fields are filled
2. Verify field values meet constraints
3. Check linked documents exist
4. Review validation error messages

---

### Issue: Cold Chain Blocking Dispense
**Symptoms**: Cannot create Stock Entry due to cold chain

**Solutions**:
1. Check cold chain logs for excursions
2. Resolve excursions (set `excursion_resolved` = 1)
3. Verify temperature is within 2-8°C
4. Check batch has valid cold chain logs

---

### Issue: Batch Not Available
**Symptoms**: Batch not showing in availability

**Solutions**:
1. Verify batch exists in PHARM-CENTRAL-COLD
2. Check batch has available quantity
3. Verify batch not expired
4. Check batch not already allocated

---

## API Endpoints

### Pharmacist Dashboard API
**Endpoint**: `/api/method/koraflow_core.api.glp1_pharmacist.get_dispense_queue`

**Purpose**: Get pending dispense tasks for pharmacist

**Response**:
```json
{
  "message": [
    {
      "name": "DISP-TASK-001",
      "patient": "PAT-001",
      "prescription": "PRES-001",
      "status": "Pending"
    }
  ]
}
```

---

### Doctor Prescription API
**Endpoint**: `/api/method/koraflow_core.api.glp1_doctor.check_contraindications`

**Purpose**: Check patient contraindications from intake

**Parameters**:
- `patient`: Patient name

**Response**:
```json
{
  "message": {
    "warnings": ["Pancreatitis history", "Kidney disease"],
    "intake_data": {...}
  }
}
```

---

### Batch Traceability API
**Endpoint**: `/api/method/koraflow_core.utils.glp1_compliance.get_batch_traceability`

**Purpose**: Get complete batch traceability

**Parameters**:
- `batch_name`: Batch number

**Response**:
```json
{
  "message": {
    "batch": "BATCH-001",
    "compounding_records": [...],
    "dispense_confirmations": [...],
    "stock_entries": [...],
    "cold_chain_logs": [...]
  }
}
```

---

## Reports

### SAHPRA Audit Report
**Location**: Reports → GLP-1 SAHPRA Audit

**Purpose**: Generate compliance audit report for SAHPRA

**Includes**:
- Dispensed quantities
- Patient counts
- Pharmacist counts
- Compounded vs. pre-packed breakdown
- Compliance metrics

---

### Batch Traceability Report
**Location**: Reports → GLP-1 Batch Traceability

**Purpose**: Detailed batch traceability report

**Includes**:
- Batch details
- Compounding history
- Dispense history
- Stock movements
- Cold chain logs

---

## Conclusion

This manual provides comprehensive guidance for testing and using the GLP-1 Dispensing Structure. Follow the step-by-step procedures to verify all features work correctly, and refer to the troubleshooting section if issues arise.

For additional support, check:
- Server logs: `bench/logs/web.log`
- Error logs: `bench/logs/error.log`
- Frappe documentation: https://frappeframework.com/docs

---

**Last Updated**: January 11, 2025
**Version**: 1.0
**Status**: Production Ready
