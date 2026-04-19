# 🔔 Internal Certificate Alert Settings - Frontend Implementation

## ✅ What Was Built

### Frontend Components Created

#### 1. **InternalCertificateAlertsPage.jsx** ✓
- Comprehensive alert configuration interface
- Expiration threshold settings
- Risk level alert controls
- Notification channel management
- Email recipient management
- Hostname monitoring selector
- Test alert functionality
- Save settings functionality

**File Location:** `/ssl_frontend/src/pages/InternalCertificateAlertsPage.jsx`

#### 2. **InternalCertificateAlertHistoryPage.jsx** ✓
- View historical alerts
- Filter by risk level (CRITICAL, HIGH, MEDIUM, LOW)
- Search by hostname/domain
- Pagination support
- Alert type display
- Formatted timestamps
- Risk level visualization

**File Location:** `/ssl_frontend/src/pages/InternalCertificateAlertHistoryPage.jsx`

### Routes Added

```
/dashboard/internal-alerts              → Alert Settings
/dashboard/internal-alerts-history      → Alert History
/admin/internal-alerts                  → Alert Settings (Admin)
/admin/internal-alerts-history          → Alert History (Admin)
```

### Navigation Links Added

```
🔔 Internal Alerts       → /dashboard/internal-alerts
📜 Alert History        → /dashboard/internal-alerts-history
```

---

## 🎛️ Alert Settings Features

### Expiration Alerts
- **Enable/Disable Toggle** - Control whether expiration alerts are active
- **Warning Threshold** - Days before expiry to trigger warning alert (1-180 days)
- **Critical Threshold** - Days before expiry to trigger critical alert (1-30 days)

### Risk Level Alerts
- **CRITICAL Risk** - Alert when certificate has CRITICAL risk level
- **HIGH Risk** - Alert when certificate has HIGH risk level
- **MEDIUM Risk** - Alert when certificate has MEDIUM risk level (optional)

### Notification Channels
- **📧 Email Notifications** - Send alerts via email
- **📱 Dashboard Notifications** - Display in dashboard
- **🔗 Webhook Integration** - Send to external webhook URL

### Alert Frequency
- **⚡ Immediate** - Alert as soon as detected
- **📅 Daily Summary** - Daily digest of alerts
- **📆 Weekly Summary** - Weekly digest of alerts

### Email Management
- Add multiple recipient email addresses
- Remove recipients individually
- Email validation included
- Visual badge display of recipients

### Hostname Monitoring
- **Monitor All** - Alert for all hostnames or specific ones
- **Select Specific Hostnames** - Choose which servers to monitor
- Scrollable list for many hostnames
- Checkbox-based selection

### Testing
- **Test Alerts Button** - Send test alert to verify configuration
- Real-time response feedback
- Validates notification channels are working

---

## 🔍 Alert History Features

### Filtering
- **Risk Level Filter** - All, CRITICAL, HIGH, MEDIUM, LOW
- **Search** - Find by hostname or domain
- **Clear Filters** - Reset all filters at once

### Display Information
- **Alert Type** - What triggered the alert (expiration, risk_high, etc.)
- **Hostname** - Which server certificate belongs to
- **Domain** - Certificate subject domain
- **Risk Level** - Color-coded risk level with emoji
- **Triggered Time** - When the alert was created
- **Details** - Alert message/description

### Visual Elements
- Color-coded risk levels
- Emojis for quick identification
- Risk badges with background colors
- Responsive table layout
- Empty state message

---

## 📱 User Interface

### Alert Settings Page Layout

**Header Section**
```
🔔 Internal Certificate Alerts
Configure alert settings for internal certificates

[📤 Test Alerts]  [💾 Save Settings]
```

**Left Column (50%)**
- ⏰ Expiration Alerts section
- 📊 Risk Level Alerts section

**Right Column (50%)**
- 📢 Notification Channels section
- ⏱️ Alert Frequency section

**Bottom Row**
- 📧 Email Recipients management
- 🖥️ Monitored Hostnames selection

### Alert History Page Layout

**Header Section**
```
📜 Alert History
View all internal certificate alerts
```

**Filter Section**
```
[🔍 Search hostname/domain]  [Select Risk Level]  [Clear Filters]
```

**Alert Table**
```
Alert Type | Hostname | Domain | Risk Level | Triggered | Details
-----------+----------+--------+------------+-----------+---------
(rows of alerts with styling)
```

---

## 🔗 API Integration Points

### Expected Backend Endpoints

```
GET  /api/internal-certificates/alert-settings/
     → Fetch current alert settings

POST /api/internal-certificates/alert-settings/
     → Save alert settings

POST /api/internal-certificates/test-alerts/
     → Send test alert

GET  /api/internal-certificates/alert-history/
     → Fetch alert history with filters
```

### Request/Response Formats

**Alert Settings Structure**
```json
{
  "enable_expiration_alerts": true,
  "expiration_threshold_days": 30,
  "critical_threshold_days": 7,
  "enable_critical_alerts": true,
  "enable_high_alerts": true,
  "enable_medium_alerts": false,
  "notification_channels": {
    "email": true,
    "dashboard": true,
    "webhook": false
  },
  "email_recipients": ["admin@example.com"],
  "webhook_url": "",
  "alert_frequency": "immediate",
  "monitored_hostnames": ["SERVER-01", "SERVER-02"],
  "all_hostnames": false
}
```

**Alert History Item**
```json
{
  "id": 123,
  "alert_type": "expiration",
  "hostname": "SERVER-01",
  "domain": "example.com",
  "risk_level": "HIGH",
  "message": "Certificate expiring in 15 days",
  "created_at": "2026-04-19T10:30:00Z"
}
```

---

## 🎨 Styling

### Colors Used
- **CRITICAL:** #c77dff (Purple)
- **HIGH:** #b078e0 (Light Purple)
- **MEDIUM:** #8127ca (Blue)
- **LOW:** #7a21d4 (Darker Blue)

### Emojis Used
```
🔔 - Alert/Notification
⏰ - Expiration/Time
🔴 - Critical risk
🟠 - High risk
🟡 - Medium risk
🟢 - Low risk
⚡ - Immediate
📅 - Daily
📆 - Weekly
📧 - Email
📱 - Dashboard
🔗 - Webhook
📢 - Notification channels
🖥️ - Hostnames/Server
💾 - Save
📤 - Test
📜 - History
🔍 - Search
⚙️ - Settings
```

---

## ✨ Key Features

### Smart State Management
- All settings managed with React hooks (useState)
- Real-time form updates
- Loading and saving states
- Error messages with feedback

### User Experience
- Tooltips and helper text for each setting
- Disabled input states when channels not selected
- Badge display for selected items
- Toast-style messages for success/error
- Visual feedback during save/test operations

### Responsive Design
- Works on desktop, tablet, mobile
- Flexible grid layout (col-lg-6 for 2-column on desktop)
- Stacked layout on smaller screens
- Scrollable lists for many items

### Accessibility
- Proper label associations
- Form controls with clear descriptions
- Loading states clearly indicated
- Error messages prominent and clear
- Keyboard navigation support (HTML form elements)

---

## 📋 Integration Checklist

### Frontend (✓ Complete)
- [x] InternalCertificateAlertsPage component
- [x] InternalCertificateAlertHistoryPage component
- [x] Routes added to App.jsx
- [x] Navigation links in AdminLayout
- [x] Styling and UI components
- [x] Form state management
- [x] Input validation
- [x] Error handling and feedback

### Backend (To Do)
- [ ] Alert settings model
- [ ] Alert history model
- [ ] API endpoints for settings CRUD
- [ ] API endpoint for test alerts
- [ ] API endpoint for alert history
- [ ] Alert generation logic
- [ ] Email sending implementation
- [ ] Webhook integration
- [ ] Serializers for request/response
- [ ] Permissions and authentication

---

## 🚀 How to Use

### For Users

1. **Navigate to Alerts**
   - Click "🔔 Internal Alerts" in sidebar
   - Or go to: `/dashboard/internal-alerts`

2. **Configure Expiration Alerts**
   - Enable/disable toggle
   - Set warning threshold (e.g., 30 days)
   - Set critical threshold (e.g., 7 days)

3. **Configure Risk Alerts**
   - Check which risk levels to alert on
   - CRITICAL and HIGH recommended

4. **Select Notification Channels**
   - Enable Email, Dashboard, Webhook as needed
   - If webhook enabled, enter URL
   - Add email recipients

5. **Choose Alert Frequency**
   - Immediate: alert right away
   - Daily: daily digest at scheduled time
   - Weekly: weekly digest

6. **Select Hostnames**
   - "Monitor all" for all servers
   - Or select specific hostnames

7. **Test and Save**
   - Click "Test Alerts" to verify configuration
   - Click "Save Settings" when satisfied

### For Developers

**File Locations**
```
Frontend:
- /ssl_frontend/src/pages/InternalCertificateAlertsPage.jsx
- /ssl_frontend/src/pages/InternalCertificateAlertHistoryPage.jsx
- /ssl_frontend/src/layouts/AdminLayout.jsx (updated)
- /ssl_frontend/src/App.jsx (updated)
```

**To extend functionality:**
1. Add new settings fields to state object
2. Add input control in JSX
3. Add to API request payload
4. Implement corresponding backend endpoint

---

## 🔧 Backend Implementation Needed

### Models to Create

```python
# alerts/models.py

class InternalCertificateAlertSettings(models.Model):
    # Expiration settings
    enable_expiration_alerts = models.BooleanField(default=True)
    expiration_threshold_days = models.IntegerField(default=30)
    critical_threshold_days = models.IntegerField(default=7)
    
    # Risk level settings
    enable_critical_alerts = models.BooleanField(default=True)
    enable_high_alerts = models.BooleanField(default=True)
    enable_medium_alerts = models.BooleanField(default=False)
    
    # Notification settings
    notification_channels = models.JSONField(default=dict)
    email_recipients = models.JSONField(default=list)
    webhook_url = models.URLField(null=True, blank=True)
    
    # Alert frequency
    alert_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='immediate'
    )
    
    # Monitored hostnames
    monitored_hostnames = models.JSONField(default=list)
    all_hostnames = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InternalCertificateAlertHistory(models.Model):
    alert_type = models.CharField(max_length=50)
    hostname = models.CharField(max_length=255, null=True, blank=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    risk_level = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### API Endpoints to Create

```python
# alerts/views.py

class AlertSettingsViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get', 'post'])
    def alert_settings(self, request):
        # GET: return current settings
        # POST: save new settings
        
    @action(detail=False, methods=['post'])
    def test_alerts(self, request):
        # Send test alert to verify configuration
        
    @action(detail=False, methods=['get'])
    def alert_history(self, request):
        # Return alert history with filtering
```

---

## 📊 Feature Summary

| Feature | Status | Location |
|---------|--------|----------|
| Alert Settings UI | ✅ Complete | InternalCertificateAlertsPage.jsx |
| Alert History UI | ✅ Complete | InternalCertificateAlertHistoryPage.jsx |
| Navigation Links | ✅ Complete | AdminLayout.jsx |
| Routes | ✅ Complete | App.jsx |
| Form Validation | ✅ Complete | Component logic |
| Error Handling | ✅ Complete | Component logic |
| API Integration | 🔄 Ready | Awaiting backend endpoints |
| Backend Models | ❌ Not Started | Needed |
| Backend Views | ❌ Not Started | Needed |
| Email Service | ❌ Not Started | Needed |
| Webhook Service | ❌ Not Started | Needed |

---

## 🎯 Next Steps

1. **Backend Development**
   - Implement alert settings models
   - Create API endpoints
   - Add alert generation logic
   - Setup email/webhook services

2. **Testing**
   - Test all form validations
   - Test API integration
   - Test alert generation
   - Test email sending

3. **Deployment**
   - Deploy frontend changes
   - Deploy backend changes
   - Configure production email settings
   - Setup webhook endpoints

---

**Status:** 🎉 Frontend Implementation Complete  
**Date:** April 19, 2026  
**Backend:** Awaiting implementation
