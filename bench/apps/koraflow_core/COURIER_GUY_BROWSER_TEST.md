# Courier Guy Integration - Browser Testing Guide

## Test Summary

The Courier Guy integration has been successfully implemented. Here's what to test:

## ✅ What Has Been Implemented

### 1. **Courier Guy Settings** (Single DocType)
- **Location**: `/app/Form/Courier Guy Settings/Courier Guy Settings`
- **Status**: ✅ Configured with API key
- **Features**:
  - API Key: `e1b2411b054d43c89b3a07895722d77b` (pre-configured)
  - API URL: `https://api.thecourierguy.co.za`
  - Integration: Enabled
  - Default pickup address fields

### 2. **Courier Guy Waybill** (DocType)
- **Location**: Search "Courier Guy Waybill" or via workspace
- **Features**:
  - Links to Delivery Notes
  - Links to Patients
  - Stores waybill and tracking numbers
  - Tracks status (Draft, Created, In Transit, Delivered, Failed)
  - Stores API responses and tracking history

### 3. **Courier Guy Workspace**
- **Location**: Workspace menu → "Courier Guy"
- **Features**:
  - Dashboard with number cards (Total, In Transit, Delivered, Pending)
  - Quick shortcuts (Settings, Waybills, New Waybill, Tracking)
  - Link cards for easy navigation
  - Live dashboard integration (attempts to fetch from Courier Guy API)

### 4. **Delivery Note Integration**
- **Location**: Any Delivery Note form
- **Features**:
  - Auto-creates waybill on Delivery Note submit
  - "Create Courier Guy Waybill" button (if not auto-created)
  - "View Waybill" button (if waybill exists)
  - "Update Tracking" button
  - "Print Waybill" button
  - Status indicators

### 5. **Patient Integration**
- **Location**: Patient form
- **Features**:
  - Shows waybill tracking on Patient dashboard
  - Displays shipment status indicators
  - Links to waybill details

### 6. **API Endpoints**
- **Public Tracking**: `/api/method/koraflow_core.koraflow_core.api.courier_guy_tracking.get_tracking_by_number`
- **Patient Tracking**: `/api/method/koraflow_core.koraflow_core.api.courier_guy_tracking.get_patient_tracking`
- **Dashboard Data**: `/api/method/koraflow_core.koraflow_core.api.courier_guy_dashboard.get_courier_guy_dashboard_data`

## 🧪 Testing Checklist

### Test 1: Access Courier Guy Settings
1. Login to ERPNext
2. Navigate to: `/app/Form/Courier Guy Settings/Courier Guy Settings`
3. **Expected**: 
   - Settings form loads
   - API Key is pre-filled
   - Integration is enabled
   - Can update pickup address details

### Test 2: Access Courier Guy Workspace
1. Login to ERPNext
2. Open Workspace menu (left sidebar)
3. Look for "Courier Guy" workspace
4. Click on it
5. **Expected**:
   - Workspace loads
   - Number cards show statistics
   - Shortcuts are visible
   - Link cards are available
   - Live dashboard section appears at top (if API endpoint exists)

### Test 3: Create Waybill from Delivery Note
1. Create a Delivery Note with:
   - Customer
   - Shipping address
   - Items
2. Submit the Delivery Note
3. **Expected**:
   - Waybill is automatically created
   - Waybill status is "Created"
   - Waybill number and tracking number are populated
   - Courier Guy buttons appear on Delivery Note form

### Test 4: Manual Waybill Creation
1. Open a submitted Delivery Note
2. Click "Create Courier Guy Waybill" button
3. **Expected**:
   - Waybill is created
   - Waybill document opens or shows success message

### Test 5: View Waybill
1. Open Courier Guy Workspace
2. Click "Waybills" shortcut or link
3. **Expected**:
   - List of waybills appears
   - Can filter and search
   - Can open individual waybills

### Test 6: Update Tracking
1. Open a waybill with tracking number
2. Click "Update Tracking" button
3. **Expected**:
   - Tracking status updates
   - Tracking history is populated
   - Status changes if shipment is delivered

### Test 7: Print Waybill
1. Open a waybill
2. Click "Print Waybill" button
3. **Expected**:
   - Print URL opens in new window
   - Or PDF is displayed

### Test 8: Patient Tracking
1. Open a Patient form
2. Check dashboard section
3. **Expected**:
   - Waybill tracking information appears
   - Status indicators show current shipment status
   - Can click to view waybill details

### Test 9: Dashboard Data
1. Open Courier Guy Workspace
2. Check "Courier Guy Live Dashboard" section
3. **Expected**:
   - Statistics cards display
   - Recent shipments table appears (if data available)
   - Refresh button works
   - If API endpoint doesn't exist, shows local ERPNext data

### Test 10: Search Functionality
1. Use search bar (press `/`)
2. Type "Courier Guy"
3. **Expected**:
   - Courier Guy Settings appears
   - Courier Guy Waybill appears
   - Can navigate to both

## 🔧 Known Issues & Notes

1. **API Endpoint**: The dashboard tries to fetch from `/api/v1/dashboard` - this may need adjustment based on actual Courier Guy API documentation
2. **Authentication**: Browser testing requires login credentials
3. **API Response Format**: The integration assumes certain response formats - may need adjustment based on actual API

## 📝 Next Steps

1. **Test with Real API**: Once you have Courier Guy API documentation, update:
   - `courier_guy_api.py` - API endpoints
   - `courier_guy_dashboard.py` - Dashboard endpoint
   
2. **Update Pickup Address**: Fill in actual business address in Courier Guy Settings

3. **Test End-to-End**: Create a real waybill and verify it appears in Courier Guy system

## 🐛 Troubleshooting

### Workspace Not Appearing
- Hard refresh browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Restart Frappe server

### Waybill Not Creating
- Check Courier Guy Settings are enabled
- Verify API key is correct
- Check error message in waybill document
- Review ERPNext error logs

### Dashboard Not Loading
- Check browser console for JavaScript errors
- Verify API endpoint is correct
- Check if Courier Guy API is accessible
- Review API response in waybill document

## ✅ Implementation Status

- ✅ Courier Guy Settings DocType
- ✅ Courier Guy Waybill DocType  
- ✅ API Client Module
- ✅ Delivery Note Hooks
- ✅ Workspace with Dashboard
- ✅ Patient Integration
- ✅ Tracking Endpoints
- ✅ Print Functionality
- ✅ UI Components (JS/CSS)

All components are implemented and ready for testing!

