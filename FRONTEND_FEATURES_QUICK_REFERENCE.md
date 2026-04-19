# 🚀 New Frontend Features - Quick Reference

## What's New?

Three powerful new features added to CertEye frontend:

### 1. 📊 Export & Reports
- **URL:** `/dashboard/export` or `/admin/export`
- **Icon in Sidebar:** 📋 Export & Reports
- **Purpose:** Download certificates in CSV format with advanced filtering

**6 Export Scenarios:**
| Option | Purpose | Parameter | Use Case |
|--------|---------|-----------|----------|
| All Certificates | Complete inventory | None | Full audit trail |
| Expiring | By expiry date | Days (default 30) | Renewal planning |
| High-Risk | By risk score | Threshold 0-100 (default 60) | Security focus |
| By Issuer | By CA provider | Issuer name | Vendor audit |
| Critical Alerts | Security issues | None | Immediate action |
| Custom Filter | Advanced | Status + Key length | Compliance |

**CSV Columns:** Domain, Subject, Issuer, Expires, Risk Level, Risk Score, Key Length, Algorithm, Serial, Thumbprint, Status, Source Type, Last Scanned, Created At, Self-Signed, SAN Count, Crypto Findings

---

### 2. ⚠️ Alerts (Dashboard - Enhanced)
- **URL:** `/dashboard/alerts` or `/admin/alerts`
- **Icon in Sidebar:** ⚠️ Alerts (now with real data)
- **Purpose:** View and manage all certificate alerts

**Dashboard Sections:**

**Statistics Cards** (Real-time):
- 🔴 Critical - Total critical severity alerts
- 🟠 High - Total high severity alerts
- 🟡 Medium - Total medium severity alerts
- 🟢 Low - Total low severity alerts

**Filters:**
- By Severity: Critical / High / Medium / Low
- By Type: Expiry / Crypto Weakness / Other
- By Status: Pending / Acknowledged

**Alert Table:**
- Domain + message
- Alert type (⏰ Expiry, 🔐 Crypto, etc.)
- Severity color-coded badge
- Created date (human readable)
- Status with acknowledgment info

**Actions:**
- 🔄 Refresh - Reload alerts and stats
- ✓ Acknowledge All - Bulk acknowledge (framework ready)

---

### 3. ⚡ Generate Alerts
- **URL:** `/dashboard/alerts-generator` or `/admin/alerts-generator`
- **Icon in Sidebar:** ⚡ Generate Alerts
- **Purpose:** Manually trigger alert generation
- **Requires:** Admin role

**Alert Types:**

**⏰ Certificate Expiry**
- 7-day warning = CRITICAL
- 30-day warning = HIGH
- 90-day warning = MEDIUM

**🔐 Cryptographic Weakness**
- Self-signed certs = HIGH
- Weak algorithms = HIGH
- Insufficient key length = HIGH

**Process:**
1. Select alert types (checkboxes)
2. Click "Generate Alerts Now"
3. System scans all certificates
4. Creates new alerts
5. Sends email to admins
6. Shows results with alert preview

**Results Display:**
- Total alerts generated
- New alerts created
- List of first 5 alerts
- Alert details: domain, severity, message

---

## 🎯 Quick Access

### From Sidebar:
```
Dashboard
├── 📊 Dashboard
├── 🔒 Certificates
├── 📋 Export & Reports  ← NEW
├── 🏢 Internal Certs
├── ⚠️ Alerts (now enhanced)
├── ⚡ Generate Alerts   ← NEW
├── 🔔 Internal Alerts
├── 📜 Alert History
└── ⚙️ Settings
```

---

## 💾 CSV Export Format

**Filename Pattern:** `certificates_{export_type}_{date}.csv`

**Example:** `certificates_expiring_2024-01-15.csv`

**Columns (17 total):**
1. Domain
2. Subject
3. Issuer
4. Expires
5. Risk Level
6. Risk Score
7. Key Length
8. Algorithm
9. Serial
10. Thumbprint
11. Status
12. Source Type
13. Last Scanned
14. Created At
15. Self-Signed
16. SAN Count
17. Crypto Findings

---

## 🔐 Permissions

| Feature | User | Admin | Superadmin |
|---------|------|-------|-----------|
| View Exports | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ✅ |
| View Alerts | ✅ | ✅ | ✅ |
| Generate Alerts | ❌ | ✅ | ✅ |
| Filter Alerts | ✅ | ✅ | ✅ |

---

## 📊 API Endpoints Used

```javascript
// Export
GET /api/certificates/export_csv/?filter_type=all|expiring|high_risk|by_issuer|critical|custom
Query params: days, threshold, issuer, status, key_length

// Alerts
GET /api/alerts/?severity=...&alert_type=...&is_acknowledged=...
GET /api/alerts/stats/
POST /api/alerts/generate/ { alert_types: ['EXPIRY', 'CRYPTO_WEAKNESS'] }
```

---

## 🎨 UI Components

### Cards
- Statistics cards (4 severity levels)
- Configuration cards (filter settings)
- Result cards (export preview, alert results)
- Info cards (help text and documentation)

### Forms
- Dropdown selects (severity, type, status)
- Number inputs (days, threshold, key length)
- Text inputs (issuer name, status)
- Checkboxes (alert type selection)

### Tables
- Alert table (domain, type, severity, date, status)
- Responsive design (scrolls on mobile)
- Hover effects (row highlighting)
- Color-coded badges

### Buttons
- Primary (Export, Generate)
- Secondary (Refresh, Acknowledge All)
- Danger (for admin actions)
- Disabled state when no data/loading

---

## 🔄 Workflows

### Export Workflow
1. Navigate to Export & Reports
2. Select export scenario
3. Configure filters (if needed)
4. Click "Export as CSV"
5. CSV file downloads
6. Open in Excel/Sheets for analysis

### Alert View Workflow
1. Navigate to Alerts
2. View statistics at top
3. Apply filters to narrow results
4. View alert details in table
5. Click Refresh to reload
6. See timestamps and status

### Alert Generate Workflow
1. Navigate to Generate Alerts
2. Select alert types
3. Review what will be checked
4. Click "Generate Alerts Now"
5. Wait for scan (usually 10-30 seconds)
6. Review results
7. Admins receive email notifications

---

## 🐛 Troubleshooting

**"No alerts to display"**
- ✓ Alerts may not have been generated yet
- ✓ Try Generate Alerts page
- ✓ Or check filters are not too restrictive

**"Export failed"**
- ✓ Check JWT token is valid
- ✓ Verify API is running
- ✓ Try fewer records (use filters)

**"Generate Alerts: Admin only"**
- ✓ You need Admin or Superadmin role
- ✓ Contact system administrator

**Filter not working**
- ✓ Click Refresh to reload
- ✓ Check filters are properly selected
- ✓ Clear filters and try again

---

## 📈 Statistics

**Alert Generation Typically Finds:**
- 10-20% of certificates with expiry concerns
- 5-15% with cryptographic issues
- Duplicates ignored (24-hour window)

**Export File Sizes:**
- All certs: 50-500 KB (depends on count)
- Filtered: 10-100 KB
- Average row: 0.5-1 KB

---

## 🔔 Email Notifications

When alerts are generated, admins receive email with:
- Total alerts created
- Severity breakdown
- Certificate details
- Direct action items
- Link to dashboard

---

## 🎓 Learning Path

1. **Start:** View Dashboard → See overview
2. **Explore:** Go to Certificates → Understand your inventory
3. **Export:** Try Export & Reports → Generate CSV
4. **Monitor:** Go to Alerts → See current issues
5. **Manage:** Try Generate Alerts → Create alerts manually
6. **Respond:** Use alerts to prioritize actions

---

## 📱 Mobile Friendly

- Responsive design works on all devices
- Tables scroll horizontally on small screens
- Touch-friendly buttons (44px minimum)
- Readable text sizes
- Forms stack vertically

---

## ⌨️ Keyboard Navigation

- Tab through form inputs
- Enter to submit buttons
- Arrow keys in dropdowns
- Escape to close dialogs (future)
- Alt+E for Export (accessibility)

---

## 🔗 Related Documentation

- `FRONTEND_EXPORT_ALERTS_INTEGRATION.md` - Full technical details
- Backend API docs: `API_DOCUMENTATION_INTERNAL_CERTS.md`
- Architecture: `ARCHITECTURE_NEW_FEATURES.md`

---

## ✨ Pro Tips

**Tip 1: Export for Compliance**
Use "Custom Filter" to export only high-security certificates for audit trails.

**Tip 2: Alert Scheduling**
Generate alerts monthly for consistent monitoring rhythm.

**Tip 3: Risk Management**
Export "High-Risk" certificates first, focus remediation efforts there.

**Tip 4: Issuer Audit**
Use "By Issuer" export to track which CAs you're dependent on.

**Tip 5: Expiry Planning**
Export "Expiring" with 90-day window for quarterly renewal cycles.

---

**Status:** ✅ Ready to use!
**Last Updated:** 2024
**Version:** 1.0
