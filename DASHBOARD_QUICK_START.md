# 🎯 Dashboard Quick Start Guide

## 🚀 Access the Dashboard

**URL**: `http://localhost:5175/dashboard`

**Prerequisites**:
- Backend running on port 8001
- Frontend running on port 5175
- Logged in with valid JWT token

---

## 📊 Dashboard Layout

### Section 1: Header
- **Title**: Certificate Dashboard
- **Subtitle**: Overview of certificate health, risk assessment, and expiration tracking
- **Refresh Button**: Updates all data in real-time

### Section 2: Summary Cards (4 cards)
```
┌─────────────────────────────────────────────────────────┐
│ 📋 Total    │ ⏱️ Expired  │ ⚠️ Expiring Soon │ 🔴 High Risk │
│   17        │    2        │      1            │     7        │
└─────────────────────────────────────────────────────────┘
```

**What They Mean**:
- **Total Certificates**: All certificates in system
- **Expired**: Already past valid_to date (days_remaining < 0)
- **Expiring Soon**: Will expire within 30 days
- **High Risk**: CRITICAL + HIGH risk level combined

### Section 3: Charts (2 side-by-side)

**Left - Bar Chart: Certificate Expiry Distribution**
```
Active          ████████████████ 14
Expiring Soon   ██ 1
Expired         ██ 2
```
- Shows 3 categories: Active, Expiring Soon (0-30 days), Expired
- Color coded: Green / Yellow / Red

**Right - Pie Chart: Risk Distribution**
```
        CRITICAL (7)
       /     \
      /       \ LOW (8)
     |  MEDIUM |
      \ (0)  /
       \     /
        HIGH (0)
```
- Shows 4 risk categories
- Color coded: Red / Orange / Yellow / Green

### Section 4: Certificate Inventory Table

**Search & Filter Bar**
```
┌────────────────────────────┐  ┌─────────────────────┐
│ Search by domain/issuer... │  │ Filter Risk Level ▼ │
└────────────────────────────┘  └─────────────────────┘
```

**Certificate Table**
```
Domain              │ Issuer           │ Risk    │ Score │ Expires    │ Days Left
─────────────────────────────────────────────────────────────────────────────────
google.com          │ DigiCert Global  │ 🟢 LOW  │ 15/100│ 2026-12-31│ 256d
facebook.com        │ DigiCert Global  │ 🔴 CRIT │100/100│ 2026-04-26│ EXPIRED
example.com         │ Example CA       │ 🟡 MED  │ 50/100│ 2026-06-15│ 57d
```

**Column Explanations**:
- **Domain**: Certificate domain/hostname
- **Issuer**: Certificate authority that issued it
- **Risk Level**: Risk classification (color-coded emoji)
- **Score**: Risk score out of 100
- **Expires**: Date certificate becomes invalid
- **Days Left**: Countdown to expiration
  - Red badge: EXPIRED
  - Yellow badge: < 30 days
  - Green badge: Active

**Pagination**:
```
Previous  Page 1  Next
```
- Shows 10 certificates per page
- Only appears if > 10 total certificates

---

## 🔍 Search & Filter Examples

### Example 1: Find All Google Certificates
1. Click search box
2. Type "google"
3. Results show all domains containing "google"

### Example 2: Find All Critical Risk Certificates
1. Click "Filter Risk Level" dropdown
2. Select "🔴 CRITICAL"
3. Table shows only CRITICAL certificates

### Example 3: Find Expiring Facebook Certificates
1. Type "facebook" in search
2. Select "All Risk Levels" (or specific level)
3. Table filters to match

### Example 4: Combine Search + Filter
1. Type "example" in search
2. Select "🟡 MEDIUM" from filter
3. Shows only example.com with MEDIUM risk

---

## 📈 Interpreting the Data

### Risk Levels (Color Coded)

| Level | Emoji | Color  | Meaning |
|-------|-------|--------|---------|
| CRITICAL | 🔴 | Red | Urgent action needed |
| HIGH | 🟠 | Orange | Should fix soon |
| MEDIUM | 🟡 | Yellow | Monitor closely |
| LOW | 🟢 | Green | No immediate action |

### Risk Score

**Scale**: 0-100

- **0-25**: Low risk (✅ Good)
- **26-50**: Medium risk (⚠️ Watch)
- **51-75**: High risk (⚠️ Fix soon)
- **76-100**: Critical risk (🔴 Urgent)

### Days Left Interpretation

```
Days Left    │ Status        │ Color  │ Action
─────────────────────────────────────────────
0 or less    │ EXPIRED       │ Red    │ Replace immediately
1-30 days    │ Expiring Soon │ Yellow │ Renew soon
> 30 days    │ Active        │ Green  │ Monitor
```

---

## 🔄 Updating Data

### Manual Refresh
- Click **"🔄 Refresh"** button in top-right
- Updates all: cards, charts, table
- Takes ~1-2 seconds

### Automatic Refresh
- Dashboard loads data on page load
- Page stays current with latest backend data

### Real-Time Updates
- Backend polls database for current stats
- Frontend reflects backend data
- No caching (always fresh)

---

## 💡 Common Tasks

### Task 1: Monitor Expiring Certificates
1. Go to Dashboard
2. Check **"Expiring Soon"** card
3. Click filter dropdown → select any level
4. Look for yellow badges (< 30 days)

### Task 2: Identify High-Risk Domains
1. Go to Dashboard
2. Click filter dropdown → select "🔴 CRITICAL"
3. Review all critical certificates
4. Sort by Days Left (if expired first)

### Task 3: Verify Certificate Health
1. Check summary cards:
   - If "Expired" > 0 → Take action
   - If "Expiring Soon" > 0 → Schedule renewal
   - If "High Risk" > 0 → Review risk levels

### Task 4: Search for Specific Domain
1. Type domain in search box
2. See all related certificates
3. Check expiration and risk status

---

## ⚙️ Settings & Options

### Filter Options
- ✅ "All Risk Levels" - Shows everything (default)
- 🔴 "CRITICAL" - Only critical certificates
- 🟠 "HIGH" - Only high risk
- 🟡 "MEDIUM" - Only medium risk
- 🟢 "LOW" - Only low risk

### Search Options
- ✅ Case-insensitive
- ✅ Searches domain AND issuer
- ✅ Real-time (no search button needed)
- ✅ Instant results

### Display Options
- ✅ Pagination: 10 items per page
- ✅ Sort: By date scanned (default)
- ✅ Columns: All always visible
- ✅ Refresh: Manual button

---

## 🎨 Visual Guide

### Colors Meaning

```
Header Background:    Light blue (#f8f9fa)
Summary Cards:        White with colored icons
Chart Background:     Light gray (#f5f5f5)
Risk Badges:
  - CRITICAL:        Red (#dc3545)
  - HIGH:            Orange (#fd7e14)
  - MEDIUM:          Yellow (#ffc107)
  - LOW:             Green (#28a745)
```

### Chart Legend

**Bar Chart Colors**:
- Red bar = Expired certificates
- Yellow bar = Expiring soon
- Green bar = Active

**Pie Chart Colors**:
- Red slice = CRITICAL
- Orange slice = HIGH
- Yellow slice = MEDIUM
- Green slice = LOW

---

## 🚨 Error Handling

### If Dashboard Won't Load

**Error**: "Loading dashboard data..."
- **Cause**: Backend slow to respond
- **Fix**: Wait 5-10 seconds, click Refresh

**Error**: "Failed to load dashboard"
- **Cause**: Not authenticated or token expired
- **Fix**: Logout and login again

**Error**: "No certificates found"
- **Cause**: No certificates in database OR filter too strict
- **Fix**: Adjust filters or scan new domain

---

## 📱 Mobile/Responsive

Dashboard adapts to screen size:

- **Desktop** (1200px+): 4-column layout
- **Tablet** (768px+): 2-column layout
- **Mobile** (< 768px): 1-column layout

Charts and table adjust width automatically.

---

## 🔗 Related Features

- **📍 Scan Domain**: `/dashboard/scan` - Scan new certificate
- **📜 Certificates**: `/dashboard/certificates` - Full certificate list
- **⚙️ Settings**: `/admin/settings` - User preferences
- **📊 Reports**: `/admin/reports` - Generate reports

---

## ✅ Verification Checklist

- ✅ 4 summary cards visible
- ✅ Bar chart showing expiry distribution
- ✅ Pie chart showing risk distribution
- ✅ Certificate table with data
- ✅ Search box works (type and see results)
- ✅ Filter dropdown works (select risk level)
- ✅ Pagination works (if > 10 certs)
- ✅ Refresh button updates data
- ✅ Colors match risk levels
- ✅ Days remaining shows correct values

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Data not updating | Click Refresh button |
| Search not working | Try shorter search term |
| Filter not working | Ensure certificate has that risk level |
| Charts not showing | Wait for page to fully load |
| Mobile layout broken | Try rotating device |
| Too many/few results | Adjust search term and filters |

---

**Version**: 1.0  
**Last Updated**: April 19, 2026  
**Status**: Ready for Use ✅
