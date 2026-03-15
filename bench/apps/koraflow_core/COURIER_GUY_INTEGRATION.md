# Courier Guy API Integration for ERPNext

This integration allows you to seamlessly create waybills, print shipping labels, and track shipments using The Courier Guy API directly from ERPNext.

## Features

- **Automatic Waybill Creation**: Automatically creates Courier Guy waybills when Delivery Notes are submitted
- **Waybill Management**: Full CRUD operations for waybills with Courier Guy API synchronization
- **Print Waybills**: Print waybill labels directly from ERPNext
- **Tracking Integration**: Real-time tracking status updates for shipments
- **Patient Tracking**: Patients can track their shipments using tracking numbers
- **Delivery Note Integration**: Seamless integration with ERPNext Delivery Notes

## Setup Instructions

### 1. Configure Courier Guy Settings

1. Navigate to **Courier Guy Settings** (Single DocType)
2. Enter your API credentials:
   - **API Key**: `e1b2411b054d43c89b3a07895722d77b`
   - **API URL**: `https://api.thecourierguy.co.za` (default)
3. Configure default pickup address:
   - Address details
   - Contact information
   - City, Suburb, Postal Code
4. Set default service type (Express, Same Day, Next Day, Economy)
5. Enable the integration by checking **Enabled**
6. Save

### 2. Install Dependencies

The integration uses the `requests` library which should already be available in ERPNext. If not, install it:

```bash
bench pip install requests
```

### 3. Migrate DocTypes

After adding the new DocTypes, run migrations:

```bash
bench migrate
bench clear-cache
```

### 4. Test the Integration

1. Create a Delivery Note with shipping address
2. Submit the Delivery Note
3. A Courier Guy Waybill should be automatically created
4. Check the waybill status and tracking number

## Usage

### Creating Waybills

#### Automatic Creation
When a Delivery Note is submitted, a waybill is automatically created if:
- Courier Guy integration is enabled
- No waybill exists for the Delivery Note

#### Manual Creation
1. Open a submitted Delivery Note
2. Click **Create Courier Guy Waybill** button
3. The waybill will be created and submitted automatically

### Viewing Waybills

1. Navigate to **Courier Guy Waybill** list
2. Open any waybill to view details
3. Check tracking status and history

### Printing Waybills

1. Open a Courier Guy Waybill
2. Click **Print Waybill** button
3. The waybill label will open in a new window

### Tracking Shipments

#### For Staff
1. Open a Courier Guy Waybill
2. Click **Update Tracking** to refresh tracking status
3. View tracking history in the dashboard

#### For Patients
Patients can track shipments using:
- **API Endpoint**: `/api/method/koraflow_core.api.courier_guy_tracking.get_tracking_by_number`
- **Parameters**: `tracking_number`
- **Access**: Public (allow_guest=True)

Example:
```
GET /api/method/koraflow_core.api.courier_guy_tracking.get_tracking_by_number?tracking_number=TRACK123
```

### Patient Tracking Integration

The integration automatically shows waybill tracking information on Patient forms:
- All waybills for a patient are displayed in the dashboard
- Tracking status indicators show current shipment status
- Click on waybills to view full details

## API Endpoints

### Public Endpoints

#### Get Tracking by Number
```
GET /api/method/koraflow_core.api.courier_guy_tracking.get_tracking_by_number
Parameters:
  - tracking_number: Courier Guy tracking number
```

### Authenticated Endpoints

#### Get Patient Tracking
```
GET /api/method/koraflow_core.api.courier_guy_tracking.get_patient_tracking
Parameters:
  - patient_name: Patient name
```

#### Get Delivery Note Tracking
```
GET /api/method/koraflow_core.api.courier_guy_tracking.get_delivery_note_tracking
Parameters:
  - delivery_note: Delivery Note name
```

## Courier Guy API Client

The integration includes a flexible API client (`CourierGuyAPI`) that handles:
- Waybill creation
- Tracking retrieval
- Waybill printing
- Waybill cancellation

### API Structure

The client is designed to work with The Courier Guy API. You may need to adjust the endpoint URLs and request/response formats based on the actual API documentation.

Current implementation assumes:
- Base URL: `https://api.thecourierguy.co.za`
- Authentication: Bearer token or API Key header
- Endpoints:
  - `POST /api/v1/waybills` - Create waybill
  - `GET /api/v1/tracking/{tracking_number}` - Get tracking
  - `GET /api/v1/waybills/{waybill_number}/print` - Get print URL

**Note**: You may need to adjust these endpoints based on the actual Courier Guy API documentation.

## Customization

### Adjusting API Endpoints

Edit `apps/koraflow_core/koraflow_core/utils/courier_guy_api.py` to match the actual Courier Guy API structure.

### Customizing Waybill Creation

Edit the `create_waybill` method in `courier_guy_waybill.py` to customize how waybills are created.

### Disabling Auto-Creation

To disable automatic waybill creation on Delivery Note submit:
1. Comment out the hook in `hooks.py`:
```python
# "Delivery Note": {
#     "on_submit": "koraflow_core.hooks.courier_guy_hooks.create_waybill_on_delivery_note_submit"
# }
```

## Troubleshooting

### Waybill Creation Fails

1. Check Courier Guy Settings are configured correctly
2. Verify API key is valid
3. Check error message in waybill document
4. Review API response in waybill's `api_response` field

### Tracking Not Updating

1. Ensure tracking number is set
2. Check API connectivity
3. Verify Courier Guy API endpoint is correct
4. Check error logs in ERPNext

### Print Not Working

1. Verify waybill was created successfully
2. Check print URL in API response
3. Ensure Courier Guy API returns valid print URLs

## Security Notes

- API keys are stored securely using ERPNext's password field type
- Public tracking endpoint is rate-limited
- All authenticated endpoints require proper permissions

## Support

For issues or questions:
1. Check ERPNext error logs
2. Review Courier Guy API documentation
3. Check waybill document for error messages
4. Verify API connectivity

## Future Enhancements

Potential improvements:
- Scheduled tracking updates
- Bulk waybill creation
- Custom print formats
- SMS/Email notifications for tracking updates
- Integration with patient portal

