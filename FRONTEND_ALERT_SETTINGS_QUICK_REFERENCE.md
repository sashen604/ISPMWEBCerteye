# 🔔 Internal Certificate Alert Settings - Quick Reference

## 📍 Where to Find Everything

### Frontend Files
```
/ssl_frontend/src/pages/
├─ InternalCertificateAlertsPage.jsx          (Alert settings configuration)
├─ InternalCertificateAlertHistoryPage.jsx    (View alert history)

/ssl_frontend/src/layouts/
├─ AdminLayout.jsx                            (Updated with nav links)

/ssl_frontend/src/
├─ App.jsx                                    (Updated with routes)
```

### Routes
```
/dashboard/internal-alerts          🔔 Configure alerts
/dashboard/internal-alerts-history  📜 View alert history
/admin/internal-alerts              🔔 Configure (admin)
/admin/internal-alerts-history      📜 View (admin)
```

### Navigation Sidebar
```
🔔 Internal Alerts        → /dashboard/internal-alerts
📜 Alert History         → /dashboard/internal-alerts-history
```

---

## 🎛️ Alert Settings Page Features

### ⏰ Expiration Alerts
```
Enable/Disable Toggle
├─ Warning Threshold: 1-180 days (default 30)
└─ Critical Threshold: 1-30 days (default 7)
```

### 📊 Risk Level Alerts
```
Checkboxes:
├─ 🔴 CRITICAL Risk Alert
├─ 🟠 HIGH Risk Alert
└─ 🟡 MEDIUM Risk Alert
```

### 📢 Notification Channels
```
Toggles:
├─ 📧 Email Notifications
├─ 📱 Dashboard Notifications
└─ 🔗 Webhook Integration
   └─ (Enter webhook URL if enabled)
```

### ⏱️ Alert Frequency
```
Radio Buttons:
├─ ⚡ Immediate (as soon as detected)
├─ 📅 Daily Summary
└─ 📆 Weekly Summary
```

### 📧 Email Recipients
```
Input + Button:
├─ Type email address
├─ Click "Add" or press Enter
└─ Shows as badges with remove button
```

### 🖥️ Monitored Hostnames
```
Toggle + Checkboxes:
├─ "Monitor all" toggle
└─ If not all:
   └─ Select specific hostnames from scrollable list
```

### Buttons
```
[📤 Test Alerts]  [💾 Save Settings]
```

---

## 📜 Alert History Page Features

### Filter Section
```
[🔍 Search hostname/domain]  [Select Risk Level]  [Clear Filters]
```

### Table Columns
```
1. Alert Type       (⏰ Expiration, ❌ Expired, 🔴 High Risk, etc.)
2. Hostname         (SERVER-01, SERVER-02, etc.)
3. Domain           (certificate subject domain)
4. Risk Level       (Color-coded with emoji: 🔴🟠🟡🟢)
5. Triggered        (Date and time)
6. Details          (Alert message/description)
```

### Filtering Options
```
Risk Levels:
├─ All Risk Levels
├─ 🔴 CRITICAL
├─ 🟠 HIGH
├─ 🟡 MEDIUM
└─ 🟢 LOW

Search:
└─ By hostname or domain (case-insensitive)
```

---

## 🔗 API Integration

### Endpoints to Create

```
# Get current settings
GET /api/internal-certificates/alert-settings/
Response: {alert settings JSON}

# Save settings
POST /api/internal-certificates/alert-settings/
Body: {alert settings JSON}
Response: {updated settings}

# Test alert
POST /api/internal-certificates/test-alerts/
Response: {"message": "Test alert sent"}

# Get alert history
GET /api/internal-certificates/alert-history/
Query params: ?risk_level=CRITICAL&search=SERVER&page=1
Response: {
  "results": [
    {
      "id": 123,
      "alert_type": "expiration",
      "hostname": "SERVER-01",
      "domain": "example.com",
      "risk_level": "HIGH",
      "message": "Certificate expiring in 15 days",
      "created_at": "2026-04-19T10:30:00Z"
    },
    ...
  ],
  "count": 42,
  "next": "...?page=2"
}
```

### Alert Settings JSON Format

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
  "email_recipients": [
    "admin@example.com",
    "security@example.com"
  ],
  "webhook_url": "https://your-webhook.com/alerts",
  "alert_frequency": "immediate",
  "monitored_hostnames": [
    "SERVER-01",
    "SERVER-02",
    "EXCHANGE-01"
  ],
  "all_hostnames": false
}
```

---

## 🎨 Design Elements

### Colors
```
🔴 CRITICAL: #c77dff (Purple)
🟠 HIGH:     #b078e0 (Light Purple)
🟡 MEDIUM:   #8127ca (Blue)
🟢 LOW:      #7a21d4 (Dark Blue)
```

### Emojis Used
```
🔔 Alert/Bell icon
⏰ Expiration/Time
🔴 Critical risk
🟠 High risk
🟡 Medium risk
🟢 Low risk
⚡ Immediate
📅 Daily
📆 Weekly
📧 Email
📱 Mobile/Dashboard
🔗 Webhook
📢 Notification/Channel
🖥️ Hostname/Server
💾 Save
📤 Test/Send
📜 History
🔍 Search
⚙️ Settings
```

---

## 💻 Code Structure

### InternalCertificateAlertsPage.jsx

**State Management**
```javascript
const [alertSettings, setAlertSettings] = useState({
  enable_expiration_alerts: true,
  expiration_threshold_days: 30,
  // ... more settings
})
```

**Key Functions**
```javascript
loadAlertSettings()        // Fetch from API
loadAvailableHostnames()   // Get list of servers
handleCheckboxChange()     // Toggle boolean settings
handleInputChange()        // Update input fields
addEmailRecipient()        // Add email with validation
removeEmailRecipient()     // Remove email from list
toggleHostname()           // Select/deselect hostname
toggleAllHostnames()       // Select all / none
saveSettings()             // POST to API
testAlerts()              // Send test alert
```

**Layout**
```
Header
├─ Title + Description
├─ [Test Alerts] [Save Settings] buttons
└─ Message alerts

Left Column (50%)
├─ Expiration Alerts
└─ Risk Level Alerts

Right Column (50%)
├─ Notification Channels
└─ Alert Frequency

Bottom (if email enabled)
├─ Email Recipients
└─ Monitored Hostnames
```

### InternalCertificateAlertHistoryPage.jsx

**State Management**
```javascript
const [alerts, setAlerts] = useState([])
const [filter, setFilter] = useState('all')     // Risk level filter
const [search, setSearch] = useState('')        // Search term
const [page, setPage] = useState(1)             // Pagination
```

**Key Functions**
```javascript
loadAlerts()              // Fetch with filters
handleSearch()            // Submit search
getRiskColor()            // Get hex color for risk level
getRiskEmoji()            // Get emoji for risk level
getAlertType()            // Get display name for alert type
formatDate()              // Format timestamp
```

**Layout**
```
Header
├─ Title + Description

Filter Section
├─ Search input
├─ Risk level dropdown
└─ Clear filters button

Alert Table
├─ Headers: Type | Hostname | Domain | Risk | Triggered | Details
└─ Rows: Alert data (empty state if no alerts)
```

---

## 🚀 How to Connect Backend

### Step 1: Create Models
```python
class InternalCertificateAlertSettings(models.Model):
    # Add all fields from alert settings JSON
```

### Step 2: Create Serializers
```python
class AlertSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalCertificateAlertSettings
        fields = '__all__'
```

### Step 3: Create ViewSet
```python
class AlertSettingsViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get', 'post'])
    def alert_settings(self, request):
        # Implement CRUD

    @action(detail=False, methods=['post'])
    def test_alerts(self, request):
        # Send test alert

    @action(detail=False, methods=['get'])
    def alert_history(self, request):
        # Return history with filtering
```

### Step 4: Register URL Routes
```python
router.register(r'internal-certificates', AlertSettingsViewSet)
# URLs will be:
# /api/internal-certificates/alert-settings/
# /api/internal-certificates/test-alerts/
# /api/internal-certificates/alert-history/
```

---

## ✅ Validation Rules

### User Inputs
```
Email Recipients:
├─ Must contain '@'
├─ Must be valid email format
└─ Duplicates are auto-removed

Webhook URL:
├─ Must be valid URL format
├─ Must start with http:// or https://
└─ Required if webhook channel enabled

Thresholds:
├─ Warning: 1-180 days
└─ Critical: 1-30 days

Hostnames:
├─ If "all_hostnames" is false
└─ At least one must be selected
```

---

## 🎯 User Workflows

### Workflow 1: Basic Setup
```
1. Go to 🔔 Internal Alerts
2. Toggle "Enable expiration alerts"
3. Set warning threshold (e.g., 30 days)
4. Set critical threshold (e.g., 7 days)
5. Check "Email Notifications"
6. Add email recipients
7. Click "Save Settings"
8. Click "Test Alerts" to verify
```

### Workflow 2: Setup Risk Alerts
```
1. Go to 🔔 Internal Alerts
2. Check "Alert on CRITICAL risk level"
3. Check "Alert on HIGH risk level"
4. Select notification channels
5. Add email recipients
6. Set alert frequency (Immediate recommended)
7. Save Settings
```

### Workflow 3: View Alert History
```
1. Go to 📜 Alert History
2. Optionally filter by risk level
3. Optionally search by hostname/domain
4. View alert table
5. Click Clear Filters to reset
```

---

## 🔧 Troubleshooting

### Settings Not Saving
- Check network tab for failed API request
- Verify backend endpoint exists: `POST /api/internal-certificates/alert-settings/`
- Check browser console for JavaScript errors

### Test Alert Not Sending
- Verify email recipients are added
- Check notification channels are enabled
- Verify backend endpoint: `POST /api/internal-certificates/test-alerts/`
- Check backend logs for email service errors

### Alert History Not Loading
- Verify backend endpoint exists: `GET /api/internal-certificates/alert-history/`
- Check network tab for API response
- Look for any JavaScript errors in console

### Hostnames Not Loading
- Check network tab for certificate list request
- Verify internal certificates exist in database
- Check filter is working correctly

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Components Created | 2 |
| Routes Added | 4 |
| Navigation Links Added | 2 |
| Lines of Code | 600+ |
| API Endpoints Required | 4 |
| Form Controls | 30+ |
| Validation Rules | 5+ |

---

## 📚 Related Documentation

- `FRONTEND_ALERT_SETTINGS_IMPLEMENTATION.md` - Full implementation details
- `INTERNAL_CERTS_STATUS.md` - System overview
- `CERTIFICATE_SERVICE_ARCHITECTURE.md` - Architecture

---

**Status:** ✅ Frontend Complete  
**Backend:** 🔄 Ready for implementation  
**Testing:** 📋 Ready for QA

*Last Updated: April 19, 2026*
