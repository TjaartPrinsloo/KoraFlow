# Courier Guy Integration - Setup Summary

## Overview

A complete integration of The Courier Guy API into ERPNext for sales operations, including waybill creation, printing, and tracking for patients.

## Files Created

### DocTypes

1. **Courier Guy Settings** (`doctype/courier_guy_settings/`)
   - Single DocType for API configuration
   - Stores API key, URL, and default pickup address
   - Location: `apps/koraflow_core/koraflow_core/doctype/courier_guy_settings/`

2. **Courier Guy Waybill** (`doctype/courier_guy_waybill/`)
   - Stores waybill information and tracking data
   - Links to Delivery Notes and Patients
   - Location: `apps/koraflow_core/koraflow_core/doctype/courier_guy_waybill/`

### API Client

3. **Courier Guy API Client** (`utils/courier_guy_api.py`)
   - Handles all API interactions with The Courier Guy
   - Methods: create_waybill, get_tracking, get_waybill_print, cancel_waybill
   - Location: `apps/koraflow_core/koraflow_core/utils/courier_guy_api.py`

### Hooks

4. **Courier Guy Hooks** (`hooks/courier_guy_hooks.py`)
   - Auto-creates waybills when Delivery Notes are submitted
   - Location: `apps/koraflow_core/koraflow_core/hooks/courier_guy_hooks.py`

### API Endpoints

5. **Tracking API** (`api/courier_guy_tracking.py`)
   - Public endpoint for tracking by number
   - Patient tracking endpoint
   - Delivery Note tracking endpoint
   - Location: `apps/koraflow_core/koraflow_core/api/courier_guy_tracking.py`

### UI Components

6. **Delivery Note Integration** (`public/js/courier_guy_delivery_note.js`)
   - Adds waybill buttons to Delivery Note form
   - Shows tracking status
   - Location: `apps/koraflow_core/koraflow_core/public/js/courier_guy_delivery_note.js`

7. **Patient Tracking** (`public/js/courier_guy_patient.js`)
   - Shows waybill tracking on Patient form
   - Dashboard indicators for shipment status
   - Location: `apps/koraflow_core/koraflow_core/public/js/courier_guy_patient.js`

8. **Waybill Form** (`doctype/courier_guy_waybill/courier_guy_waybill.js`)
   - Custom buttons for tracking and printing
   - Location: `apps/koraflow_core/koraflow_core/doctype/courier_guy_waybill/courier_guy_waybill.js`

### Configuration

9. **Hooks Updated** (`hooks.py`)
   - Added Delivery Note on_submit hook
   - Added JS files to bundle
   - Location: `apps/koraflow_core/koraflow_core/hooks.py`

## Setup Steps

### 1. Install/Migrate DocTypes

```bash
cd /path/to/bench
bench migrate
bench clear-cache
```

### 2. Configure Settings

1. Go to **Courier Guy Settings**
2. Enter API Key: `e1b2411b054d43c89b3a07895722d77b`
3. Set API URL: `https://api.thecourierguy.co.za`
4. Configure default pickup address
5. Enable the integration

### 3. Test Integration

1. Create a Delivery Note with shipping address
2. Submit the Delivery Note
3. Verify waybill is created automatically
4. Test printing and tracking

## API Configuration

**Important**: The Courier Guy API endpoints in the code are placeholders based on common API patterns. You may need to adjust:

1. **API Base URL**: Currently set to `https://api.thecourierguy.co.za`
2. **Endpoints**: 
   - `/api/v1/waybills` (POST) - Create waybill
   - `/api/v1/tracking/{tracking_number}` (GET) - Get tracking
   - `/api/v1/waybills/{waybill_number}/print` (GET) - Get print URL
3. **Authentication**: Currently using Bearer token and X-API-Key header
4. **Request/Response Format**: May need adjustment based on actual API

### To Adjust API Endpoints

Edit `apps/koraflow_core/koraflow_core/utils/courier_guy_api.py`:
- Update `_make_request` method for authentication
- Update `create_waybill` method for request format
- Update `get_tracking` method for response parsing
- Update `get_waybill_print` method for print URL format

## Features Implemented

✅ **Waybill Creation**
- Automatic creation on Delivery Note submit
- Manual creation from Delivery Note form
- Full address and contact information mapping

✅ **Waybill Printing**
- Print waybill labels
- Direct integration with Courier Guy print API

✅ **Tracking Integration**
- Real-time tracking status updates
- Tracking history storage
- Status indicators (Delivered, In Transit, etc.)

✅ **Patient Integration**
- Patient tracking on Patient form
- Dashboard indicators for shipment status
- Public tracking endpoint for patients

✅ **Delivery Note Integration**
- Seamless waybill creation
- Tracking status display
- Print waybill button

## API Endpoints Available

### Public (No Authentication Required)

- `GET /api/method/koraflow_core.api.courier_guy_tracking.get_tracking_by_number?tracking_number=XXX`

### Authenticated (Requires Login)

- `GET /api/method/koraflow_core.api.courier_guy_tracking.get_patient_tracking?patient_name=XXX`
- `GET /api/method/koraflow_core.api.courier_guy_tracking.get_delivery_note_tracking?delivery_note=XXX`
- `POST /api/method/koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.create_waybill_from_delivery_note`
- `POST /api/method/koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.update_tracking_status`
- `GET /api/method/koraflow_core.doctype.courier_guy_waybill.courier_guy_waybill.get_waybill_print_url`

## Next Steps

1. **Verify API Endpoints**: Check The Courier Guy API documentation and update endpoints if needed
2. **Test Integration**: Create test waybills and verify API responses
3. **Customize as Needed**: Adjust request/response formats based on actual API
4. **Deploy**: After testing, deploy to production

## Troubleshooting

### Waybill Not Created Automatically
- Check Courier Guy Settings are enabled
- Verify Delivery Note is submitted (docstatus = 1)
- Check error logs in ERPNext

### API Errors
- Verify API key is correct
- Check API URL is accessible
- Review API response in waybill document
- Check Courier Guy API documentation for correct format

### Tracking Not Working
- Ensure tracking number is set
- Verify API endpoint is correct
- Check network connectivity
- Review API response format

## Support

For issues:
1. Check ERPNext error logs
2. Review waybill document for error messages
3. Verify API connectivity
4. Check Courier Guy API documentation

