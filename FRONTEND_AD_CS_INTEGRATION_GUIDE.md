# AD CS Component Integration - Frontend Setup Guide

## ✅ Integration Complete!

The AD CS component has been integrated into your CertEye frontend application. Here's what was added:

---

## 📍 Where to Access It

### In the Application
1. **Login** as a superadmin/admin user
2. Go to **Admin Panel** (in the left sidebar)
3. Click **🏢 AD CS Management** (new menu item)
4. You'll see the AD CS management interface

### Direct URL
```
http://localhost:5173/admin/adcs
```

---

## 🔧 Files Added/Modified

### New Files Created
1. **`ssl_frontend/src/pages/ADCSManagementPage.jsx`** (9 lines)
   - Simple wrapper page for the AD CS component
   - Imports ADCSSourceForm and includes CSS

### Files Modified
1. **`ssl_frontend/src/App.jsx`**
   - Added import for `ADCSManagementPage`
   - Added new route: `/admin/adcs`

2. **`ssl_frontend/src/layouts/AdminLayout.jsx`**
   - Added menu item for superadmin/admin users
   - Shows "🏢 AD CS Management" in sidebar when user is superadmin/admin

### Already Existed (No Changes Needed)
- `ssl_frontend/src/components/ADCSSourceForm.jsx` (420 lines) - Main component
- `ssl_frontend/src/styles/adcs.css` (380 lines) - Styling

---

## 🎯 Features Available

### In the AD CS Management Page

1. **Register New AD CS Source**
   - Server hostname and IP
   - Certificate Authority name
   - Service account credentials (securely encrypted)
   - Authentication method selection (WinRM/LDAP/Agent)
   - Port and SSL configuration
   - Auto-sync settings

2. **Manage Registered Sources**
   - View all registered AD CS servers
   - Connection status indicators
   - Certificate count display
   - Last sync timestamp

3. **Test Connectivity**
   - Click "Test Connection" to validate server access
   - See connection test results
   - Troubleshoot connectivity issues

4. **Sync Certificates**
   - Click "Sync Now" to fetch certificates from AD CS
   - View import statistics
   - See which certificates were imported/updated/failed
   - Track sync duration

5. **View Sync History**
   - See all past sync operations
   - Status of each sync (success/failed/partial)
   - Certificates imported/updated/failed count
   - Sync details and error messages

---

## 🔐 Security Notes

### For End Users
- Only **superadmin/admin** users can access AD CS Management
- Passwords are securely encrypted (AES-256-GCM)
- Never displayed in the UI
- All operations are logged for audit purposes

### For Developers
- Component uses existing `api.js` client for API calls
- Authentication token automatically included via API client
- Permission checks enforced on backend
- Access restricted to admin routes

---

## 🚀 How to Access (Step by Step)

### 1. Start the Frontend
```bash
cd ssl_frontend
npm run dev
```

### 2. Login
- URL: `http://localhost:5173/login`
- Username: `superadmin`
- Password: `Admin@123456` (or your configured password)

### 3. Navigate to AD CS Management
- Click **Admin Panel** in sidebar (bottom of menu)
- Click **🏢 AD CS Management**
- Or go directly to: `http://localhost:5173/admin/adcs`

---

## 🔌 API Integration

The component uses the following backend API endpoints:

```
GET    /api/certificates/adcs-sources/
POST   /api/certificates/adcs-sources/
GET    /api/certificates/adcs-sources/{id}/
PATCH  /api/certificates/adcs-sources/{id}/
DELETE /api/certificates/adcs-sources/{id}/
POST   /api/certificates/adcs-sources/{id}/test_connection/
POST   /api/certificates/adcs-sources/{id}/sync/
GET    /api/certificates/adcs-sources/{id}/sync_history/
GET    /api/certificates/adcs-sources/{id}/connection_tests/
```

All endpoints require authentication and superadmin/admin role.

---

## 📱 Responsive Design

The component is fully responsive:
- **Desktop**: Two-panel layout (form + sources list)
- **Tablet**: Single column, stacked layout
- **Mobile**: Full-width, optimized for touch

---

## 🎨 Styling

The component uses:
- **Colors**: Blue (#0066cc) primary, green (#28a745) success, red (#dc3545) danger
- **Font**: Consistent with CertEye theme
- **Layout**: CSS Grid with responsive breakpoints
- **Animations**: Smooth hover effects and transitions

---

## 🐛 Troubleshooting

### Component Not Showing in Menu
- **Solution**: Make sure you're logged in as **superadmin** or **admin**
- Check user role in profile

### API Errors
- **401 Unauthorized**: Re-login, token may have expired
- **403 Forbidden**: User doesn't have admin permissions
- **500 Server Error**: Check backend logs

### Connection Issues
- Ensure backend is running on port 8000/8001
- Check CORS settings in Django
- Verify API client configuration in `api.js`

---

## 📚 Component Structure

```
ADCSManagementPage.jsx (wrapper page)
  └── ADCSSourceForm.jsx (main component)
      ├── Registration Form
      ├── Sources List
      ├── Connection Test Results
      ├── Sync Results Display
      └── Sync History Table

Styles:
  └── adcs.css (comprehensive styling)
```

---

## ✨ Next Steps

1. **Test the component**
   - Register a test AD CS source
   - Test connection
   - Try manual sync (will use mock data in development)

2. **Configure for production**
   - Update server details
   - Set up service accounts
   - Configure auto-sync intervals

3. **Monitor sync operations**
   - Check sync history regularly
   - Review imported certificates
   - Monitor error messages

---

## 📖 Related Documentation

- **Full Implementation Details**: `AD_CS_IMPLEMENTATION_COMPLETE.md`
- **Quick Reference**: `AD_CS_QUICK_REFERENCE.md`
- **Backend API**: Backend serializers and views in `ssl_backend/apps/certificates/`

---

**Status**: ✅ Ready to Use  
**Last Updated**: Today  
**Version**: 1.0
