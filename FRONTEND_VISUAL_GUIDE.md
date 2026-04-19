# 🎨 Frontend Features - Visual Guide

## Navigation Layout

```
┌─────────────────────────────────────────────────────────┐
│ 🔐 CertEye                      SSL Certificate Mgmt    │
│ [User Role]                                  [Logout]   │
├─────────────┬───────────────────────────────────────────┤
│             │                                           │
│ 📊 Dashboard│  Dashboard Content                       │
│ 🔒 Certs   │  (Current page shown here)              │
│ 📋 Export  │                                           │
│ 🏢 Internal│                                           │
│ ⚠️ Alerts   │                                           │
│ ⚡ Generate│                                           │
│ 🔔 Int.Alts                                            │
│ 📜 History │                                           │
│ ⚙️ Settings│                                           │
│             │                                           │
│ [ADMIN]     │                                           │
│ 👨‍💼 Admin   │                                           │
│ 👥 Users   │                                           │
│ 🏢 ADCS    │                                           │
└─────────────┴───────────────────────────────────────────┘
```

---

## Feature 1: Export & Reports Page

### Layout Diagram

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Certificate Export                                       │
│ Download certificates in CSV format with advanced filtering  │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ ┌──────────────────────┐  ┌──────────────────────────────┐ │
│ │ Export Scenarios     │  │ Configuration & Export       │ │
│ │                      │  │                              │ │
│ │ 📋 All Certificates  │  │ 📋 All Certificates         │ │
│ │    Export all        │  │ Complete inventory export    │ │
│ │                      │  │                              │ │
│ │ ⏰ Expiring [SELECTED]│  │ Configuration:               │ │
│ │    Expiring within N  │  │ [No parameters needed]       │ │
│ │    days              │  │                              │ │
│ │                      │  │ [⬇️ Export as CSV]           │ │
│ │ ⚠️ High-Risk         │  │                              │ │
│ │    By risk threshold │  │ 💡 Format: CSV file          │ │
│ │                      │  │ 📅 Name: certificates_all_...│ │
│ │ 🏢 By Issuer        │  │                              │ │
│ │    By CA provider    │  │                              │ │
│ │                      │  │                              │ │
│ │ 🔴 Critical Alerts   │  │                              │ │
│ │    Security issues   │  │                              │ │
│ │                      │  │                              │ │
│ │ ⚙️ Custom Filter     │  │                              │ │
│ │    Advanced options  │  │                              │ │
│ │                      │  │                              │ │
│ └──────────────────────┘  └──────────────────────────────┘ │
│                                                              │
│ ✨ Available Export Scenarios                              │
│ ┌──────────────────────┬─────────────────────────────────┐ │
│ │ 🎯 All: Full export  │ ⏰ Expiry: Renewal planning  │ │
│ │ ⚠️ Risk: Security    │ 🏢 Issuer: Vendor audits   │ │
│ │ 🔴 Critical: Urgent  │ ⚙️ Custom: Compliance      │ │
│ └──────────────────────┴─────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User selects scenario
      ↓
[Form shows parameters if needed]
      ↓
User configures filters
      ↓
Clicks "Export as CSV"
      ↓
API request to /api/certificates/export_csv/
      ↓
Backend generates CSV (17 columns)
      ↓
Browser downloads file
      ↓
File: certificates_{type}_{date}.csv
```

---

## Feature 2: Alerts Dashboard

### Layout Diagram

```
┌────────────────────────────────────────────────────────────┐
│ 🚨 Alert Management                        🔄 Refresh      │
│ Review and manage certificate security alerts  ✓ Ack All   │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ Statistics Cards:                                            │
│ ┌──────────────────┬──────────────────┬─────────────────┐ │
│ │ 🔴 Critical      │ 🟠 High          │ 🟡 Medium       │ │
│ │ 5 alerts         │ 12 alerts        │ 8 alerts        │ │
│ └──────────────────┴──────────────────┴─────────────────┘ │
│ ┌──────────────────┐                                       │
│ │ 🟢 Low           │                                       │
│ │ 3 alerts         │                                       │
│ └──────────────────┘                                       │
│                                                              │
│ Filters:                                                    │
│ ┌──────────────────┬──────────────────┬─────────────────┐ │
│ │ Severity:        │ Alert Type:      │ Status:         │ │
│ │ [All ▼]          │ [All ▼]          │ [All ▼]         │ │
│ │ 🔴 Critical      │ ⏰ Expiry        │ ⏳ Pending      │ │
│ │ 🟠 High          │ 🔐 Crypto       │ ✓ Acknowledged │ │
│ │ 🟡 Medium        │ 📌 Other        │                 │ │
│ │ 🟢 Low           │                  │                 │ │
│ └──────────────────┴──────────────────┴─────────────────┘ │
│                                                              │
│ Alerts Table (📋 Alerts - 28 total):                       │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Certificate Domain        │ Type    │ Severity │ ... │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ example.com               │ ⏰ Exp. │ 🔴 CRIT │ ... │ │
│ │ Expires in 5 days         │         │         │     │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ api.domain.net            │ 🔐 Cry │ 🟠 HIGH │ ... │ │
│ │ Self-signed certificate   │         │         │     │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ cdn.service.io            │ ⏰ Exp. │ 🟡 MED  │ ... │ │
│ │ Expires in 45 days        │         │         │     │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                              │
│ 💡 Alert Types: Expiry (upcoming) | Crypto (weak keys)    │
└────────────────────────────────────────────────────────────┘
```

### Filter Workflow

```
View All Alerts
      ↓
Filter by Severity: "Critical"
      ↓
[5 alerts shown]
      ↓
Further filter by Type: "Expiry"
      ↓
[2 critical expiry alerts shown]
      ↓
Click Refresh for latest
      ↓
Alert counts/data updated
```

---

## Feature 3: Generate Alerts

### Layout Diagram

```
┌────────────────────────────────────────────────────────────┐
│ ⚡ Alert Generator                                           │
│ Manually trigger alert generation for certificate issues   │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│ ┌──────────────────────┐  ┌──────────────────────────────┐ │
│ │ Alert Types to Gen.  │  │ Generate Alerts              │ │
│ │                      │  │                              │ │
│ │ ☑ ⏰ Expiry Alerts  │  │ ⚠️ Admin Only               │ │
│ │ Detect within        │  │                              │ │
│ │ 7/30/90 day windows  │  │ [⚡ Generate Alerts Now]   │ │
│ │                      │  │                              │ │
│ │ ☑ 🔐 Crypto         │  │ 💡 Process:                 │ │
│ │ Weak algorithms,     │  │ • Scan all certs           │ │
│ │ insufficient keys,   │  │ • Check conditions         │ │
│ │ self-signed certs    │  │ • Create alerts            │ │
│ │                      │  │ • Send emails              │ │
│ │                      │  │                              │ │
│ │ ✓ Selected:         │  │ Results:                     │ │
│ │ ⏰ Expiry            │  │ ┌────────────────────────┐ │ │
│ │ 🔐 Crypto           │  │ │ ✓ Generation Complete  │ │
│ │                      │  │ │                        │ │
│ │                      │  │ │ Total: 15 alerts       │ │
│ │                      │  │ │ New: 7 alerts          │ │
│ │                      │  │ │                        │ │
│ │                      │  │ │ Recent:                │ │
│ │                      │  │ │ • api.domain.com       │ │
│ │                      │  │ │   CRITICAL - Expiry    │ │
│ │                      │  │ │ • service.io           │ │
│ │                      │  │ │   HIGH - Self-signed   │ │
│ │                      │  │ │ +5 more...             │ │
│ │                      │  │ └────────────────────────┘ │ │
│ └──────────────────────┘  └──────────────────────────────┘ │
│                                                              │
│ 📚 Alert Type Reference                                    │
│ ┌──────────────────────┬──────────────────────────────┐ │
│ │ ⏰ Expiry            │ 🔐 Crypto Weakness           │ │
│ │ • 7-day Critical     │ • Self-signed: HIGH          │ │
│ │ • 30-day High        │ • Weak algo: HIGH            │ │
│ │ • 90-day Medium      │ • Weak key: HIGH             │ │
│ └──────────────────────┴──────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Generation Process

```
Admin selects alert types
      ↓
Clicks "Generate Alerts Now"
      ↓
API sends alert_types to backend
      ↓
System scans all certificates:
  • Check expiry dates (7/30/90 day windows)
  • Check algorithms (weak ones)
  • Check key lengths (insufficient)
  • Check for self-signed
      ↓
Creates Alert objects for matches
      ↓
Deduplicates (24-hour window)
      ↓
Sends email notifications to admins
      ↓
Returns result with alert list
      ↓
Frontend shows results in card
      ↓
Admin can:
  • View statistics
  • See alert preview
  • Navigate to Alerts dashboard
```

---

## Color Coding System

### Severity Colors
```
🔴 CRITICAL  = Red       #c77dff (Urgent - Act immediately)
🟠 HIGH      = Orange    #b078e0 (Important - High priority)
🟡 MEDIUM    = Yellow    #8127ca (Moderate - Schedule action)
🟢 LOW       = Green     #7a21d4 (Low - Monitor)
```

### Status Badges
```
✓ Acknowledged = Green badge (DONE)
⏳ Pending      = Yellow badge (TODO)
🔄 Loading     = Spinner (WAIT)
❌ Error       = Red alert (FAILED)
ℹ️ Info        = Blue alert (INFO)
```

---

## CSV Export Example

### File: `certificates_expiring_2024-01-15.csv`

```
Domain,Subject,Issuer,Expires,Risk Level,Risk Score,Key Length,Algorithm,Serial,...
example.com,*.example.com,Let's Encrypt,2024-02-01,MEDIUM,45,2048,RSA-2048,123456,...
api.domain.io,api.domain.io,DigiCert,2024-03-15,HIGH,72,2048,SHA256,789012,...
cdn.service.net,*.service.net,Let's Encrypt,2024-03-20,LOW,25,4096,RSA-4096,345678,...
```

**Columns (17):**
1. Domain
2. Subject
3. Issuer
4. Expires (date)
5. Risk Level (CRITICAL/HIGH/MEDIUM/LOW)
6. Risk Score (0-100)
7. Key Length (bits)
8. Algorithm (RSA/ECDSA)
9. Serial Number
10. Thumbprint
11. Status (Active/Expired/Revoked)
12. Source Type (External/Internal/ADCS)
13. Last Scanned
14. Created At
15. Self-Signed (yes/no)
16. SAN Count
17. Crypto Findings

---

## User Interaction Flow

### Scenario: Certificate Renewal Planning

```
STEP 1: Export expiring certs
└─→ Go to "Export & Reports"
    └─→ Select "Expiring Certificates"
        └─→ Set "30 days" window
            └─→ Click "Export as CSV"
                └─→ Get: certificates_expiring_2024-01-15.csv

STEP 2: Analyze in Excel
└─→ Open CSV file
    └─→ Sort by "Expires" date
        └─→ Find renewal deadlines
            └─→ Plan renewal schedule

STEP 3: Track in Alerts
└─→ Go to "Alerts" page
    └─→ Filter by "Expiry" type
        └─→ See statistics (e.g., 5 critical)
            └─→ Review each alert
                └─→ Plan remediation

STEP 4: Monitor Progress
└─→ Click "Refresh" on Alerts page
    └─→ See updated statistics
        └─→ Alert counts decrease as certs renew
            └─→ Success when all gone!
```

---

## Common Tasks

### Task 1: Find Expiring Certificates
```
Click: Export & Reports
  ↓
Select: Expiring Certificates
  ↓
Set: 90 days
  ↓
Export
  ↓
Result: CSV with certificates expiring in 90 days
```

### Task 2: Check Critical Issues
```
Click: Alerts
  ↓
Filter: Severity = Critical
  ↓
Filter: Type = Crypto Weakness
  ↓
Result: See critical crypto issues
```

### Task 3: Generate Fresh Alerts
```
Click: Generate Alerts
  ↓
Check: Expiry + Crypto boxes
  ↓
Click: Generate Alerts Now
  ↓
Wait: System scans (10-30 sec)
  ↓
Result: See new alerts + email sent
```

### Task 4: Vendor Audit
```
Click: Export & Reports
  ↓
Select: By Issuer
  ↓
Type: "Let's Encrypt"
  ↓
Export
  ↓
Result: CSV with all Let's Encrypt certs
```

---

## Mobile Responsive Layout

### Mobile View (< 768px)

```
┌──────────────────────┐
│ 🔐 CertEye           │
│ ≡ (Menu)             │
├──────────────────────┤
│ 📊 Alert Management  │
│                      │
│ [Stats stacked]      │
│ 🔴 5                 │
│ 🟠 12                │
│ 🟡 8                 │
│ 🟢 3                 │
│                      │
│ [Filters stacked]    │
│ Severity: [All ▼]    │
│ Type: [All ▼]        │
│ Status: [All ▼]      │
│                      │
│ [Table scrolls →]    │
│ Domain    │ Type │   │
│ example.. │ ⏰ E │   │
│ api...    │ 🔐 C │   │
│                      │
│ [🔄 Refresh]         │
│ [✓ Ack All]          │
└──────────────────────┘
```

---

## Accessibility Features

```
✓ Semantic HTML (form, table, button)
✓ ARIA labels where needed
✓ Color not only differentiator (emoji + text)
✓ Keyboard navigation (Tab, Enter, Arrow keys)
✓ Focus indicators visible
✓ Alt text via emoji + description
✓ Screen reader friendly
✓ High contrast ratio
✓ Readable font sizes
```

---

## Performance Metrics

```
Export Page Load:    < 1 second
Alerts Load:         < 2 seconds
Alert Generation:    10-30 seconds (background)
CSV Download:        < 5 seconds (typical)
Filter Response:     < 500ms (instant)
Mobile Performance:  Optimized
```

---

## Error Handling Examples

### Scenario: API Error

```
User: Clicks "Export as CSV"
  ↓
System: API call fails (e.g., server down)
  ↓
Frontend: Shows error message
  "Failed to export certificates"
  ↓
User: Sees message for 3-5 seconds
  ↓
User: Can dismiss or try again
```

### Scenario: Loading State

```
User: Clicks "Generate Alerts Now"
  ↓
System: Shows spinner
  "Generating Alerts..."
  ↓
Button: Becomes disabled
  ↓
User: Waits (typically 10-30 seconds)
  ↓
System: Shows results
```

---

## Tips & Tricks

### 💡 Tip 1: Export Regularly
Generate weekly exports for trend analysis.

### 💡 Tip 2: Filter First
Use filters to narrow results before export.

### 💡 Tip 3: Check After Generation
Always refresh alerts after generating.

### 💡 Tip 4: Export for Compliance
Keep copies for audit trails.

### 💡 Tip 5: Set Reminders
Schedule monthly alert generations.

---

This visual guide complements the detailed documentation!
