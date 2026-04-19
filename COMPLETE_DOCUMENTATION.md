# 📚 CERTEYE - COMPLETE DOCUMENTATION

**Last Updated:** April 19, 2026  
**Status:** ✅ PRODUCTION READY  
**Version:** 1.0 Complete

---

## 📖 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Features Implemented](#features-implemented)
3. [Architecture](#architecture)
4. [Alerts System](#alerts-system)
5. [AD CS Integration](#ad-cs-integration)
6. [Dashboard](#dashboard)
7. [Certificate Management](#certificate-management)
8. [Security & Audit Logging](#security--audit-logging)
9. [API Reference](#api-reference)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)

---

## 📋 PROJECT OVERVIEW

### What is CertEye?

CertEye is a **comprehensive SSL/TLS certificate management and monitoring system** designed to:

✅ Discover and inventory certificates from multiple sources
✅ Monitor certificate expiry and crypto weakness
✅ Generate intelligent alerts for certificate issues
✅ Integrate with Active Directory Certificate Services (AD CS)
✅ Provide risk scoring and compliance reporting
✅ Track all changes with complete audit trails

### Key Statistics

- **Backend:** Django REST Framework (Python)
- **Frontend:** React + Vite (JavaScript)
- **Database:** PostgreSQL
- **Total Files:** 150+ Python files, 50+ React components
- **Documentation:** 70+ guides (now consolidated into this file)
- **Status:** ✅ PRODUCTION READY

---

## 🎯 FEATURES IMPLEMENTED

### 1. **Alerts Management System** ✅

#### What It Does
- Real-time alert generation for certificate issues
- Multi-criteria filtering and search
- Interactive expandable alert cards
- Severity-based urgency indicators

#### Key Components

**Statistics Cards:**
- 🔴 Critical Alerts
- 🟠 High Priority Alerts
- 🟡 Medium Alerts
- 🟢 Low Priority Alerts

**Search & Filtering:**
- Full-text search across domains, messages, severity
- Filter by: Severity, Alert Type, Status
- Sort by: Date, Severity, Domain
- Smart filter combinations

**Alert Details:**
- Expandable cards with full information
- Recommended actions based on urgency
- Acknowledged status tracking
- Timeline information

#### Files:
- `ssl_frontend/src/pages/AlertsPage.jsx` (665 lines)
- Backend: `/api/alerts/` endpoints

#### Status: ✅ COMPLETE & ENHANCED

---

### 2. **Dashboard** ✅

#### What It Does
- Real-time certificate statistics
- Visual charts (Bar chart for expiry, Pie chart for risk)
- Certificate inventory table with search
- Recent alerts panel

#### Key Features

**Summary Cards:**
- Total certificates count
- Expired certificates
- Certificates expiring soon
- High-risk certificates

**Charts:**
- Bar chart: Expiry distribution (Expired/Expiring/Active)
- Pie chart: Risk level distribution (CRITICAL/HIGH/MEDIUM/LOW)

**Certificate Table:**
- Domain, Issuer, Risk Level, Expiry Date
- Search and filter functionality
- Color-coded risk indicators
- Days until expiry calculation

#### Status: ✅ COMPLETE & OPERATIONAL

---

### 3. **Certificate Scanning** ✅

#### What It Does
- Scan public SSL/TLS certificates from domains
- Extract certificate details and metadata
- Validate certificate chains
- Detect cryptocurrency/weak cryptography

#### Features
- Single or bulk domain scanning
- Automatic risk assessment
- Certificate chain validation
- Support for SNI (Server Name Indication)
- Real-time status updates

#### API Endpoints
```
POST /api/certificates/scan/
POST /api/certificates/scan-bulk/
GET /api/certificates/scan-status/{scan_id}/
```

#### Status: ✅ COMPLETE & TESTED

---

### 4. **AD CS Integration** ✅

#### What It Does
- Connect to Active Directory Certificate Services
- Discover internal certificates
- Import certificates into CertEye
- Track sync history and statistics

#### How It Works

```
CertEye Server
    ↓ (WinRM/LDAP/SSH)
Windows AD CS Server
    ↓
Extract certificates
    ↓
Import to database
    ↓
Calculate risk scores
    ↓
Generate alerts
```

#### Connection Methods
1. **WinRM** - PowerShell remoting (port 5985/5986)
2. **LDAP** - Active Directory queries (port 389/636)
3. **SSH** - Remote script execution (port 22)

#### API Endpoints
```
POST /api/adcs-connectors/
GET /api/adcs-connectors/
POST /api/adcs-connectors/{id}/test/
POST /api/adcs-connectors/{id}/sync/
GET /api/internal-certificates/
```

#### Status: ✅ COMPLETE & PRODUCTION READY

---

### 5. **Risk Scoring Engine** ✅

#### What It Does
- Automatically assess certificate risk (0-100)
- Categorize risk levels: CRITICAL, HIGH, MEDIUM, LOW
- Generate specific risk findings
- Support multiple risk criteria

#### Risk Factors

**Expiry Risk (0-50 points):**
- Days < 7: 50 points (CRITICAL)
- Days < 30: 35 points (HIGH)
- Days < 90: 20 points (MEDIUM)
- Days ≥ 90: 5 points (LOW)

**Crypto Risk (0-50 points):**
- MD5/SHA1: 50 points (BROKEN)
- Key < 2048: 40 points (WEAK)
- SHA256/RSA2048: 5 points (GOOD)
- RSA4096/ECDSA: 0 points (EXCELLENT)

**Status Risk (0-20 points):**
- Revoked: 20 points (CRITICAL)
- Pending: 10 points (MEDIUM)
- Issued: 0 points (OK)

#### Score Interpretation
- 0-30: LOW (🟢)
- 31-60: MEDIUM (🟡)
- 61-85: HIGH (🟠)
- 86-100: CRITICAL (🔴)

#### Status: ✅ COMPLETE & OPERATIONAL

---

### 6. **Audit Logging** ✅

#### What It Does
- Track all user actions and system changes
- Record certificate modifications
- Log API access and authentication
- Maintain compliance audit trail

#### Logged Events
- User login/logout
- Certificate import/export
- Certificate scanning operations
- AD CS sync operations
- Alert acknowledgment
- Setting changes
- User management actions

#### Database Tables
- `AuditLog` - Main audit trail
- `CertificateAuditLog` - Certificate-specific changes
- `ScanHistory` - Certificate scanning operations
- `ADCSSyncHistory` - AD CS sync operations

#### Status: ✅ COMPLETE & TESTED

---

### 7. **User Authentication & Authorization** ✅

#### User Roles
1. **SuperAdmin** - Full system access
2. **Admin** - Manage users, settings, connectors
3. **Manager** - View all data, acknowledge alerts
4. **Viewer** - Read-only access

#### Features
- JWT token-based authentication
- Role-based access control (RBAC)
- Secure password hashing (bcrypt)
- Session management
- Permission-based API endpoints

#### Status: ✅ COMPLETE & SECURE

---

## 🏗️ ARCHITECTURE

### System Overview

```
┌─────────────────────────────────────────┐
│        React Frontend (Vite)            │
│  - Dashboard                            │
│  - Alerts Management                    │
│  - Certificate Inventory                │
│  - AD CS Connector Management           │
└────────────────┬────────────────────────┘
                 │ HTTP/REST API
                 ↓
┌─────────────────────────────────────────┐
│     Django REST Backend                 │
│  - Authentication                       │
│  - Certificate Management               │
│  - Alert Generation                     │
│  - AD CS Integration                    │
│  - Risk Scoring                         │
│  - Audit Logging                        │
└────────────────┬────────────────────────┘
                 │ SQL Queries
                 ↓
┌─────────────────────────────────────────┐
│      PostgreSQL Database                │
│  - Certificates                         │
│  - Alerts                               │
│  - Users & Roles                        │
│  - Audit Logs                           │
│  - AD CS Connectors                     │
└─────────────────────────────────────────┘
```

### Database Schema

**Main Tables:**
- `users` - User accounts and authentication
- `certificates` - SSL/TLS certificate inventory
- `alerts` - Generated alerts
- `internal_certificates` - AD CS discovered certs
- `adcs_connectors` - AD CS server configurations
- `adcs_sync_history` - Sync operation records
- `audit_logs` - System audit trail

### API Architecture

**REST Endpoints:**

```
Authentication:
  POST /api/auth/login
  POST /api/auth/logout
  POST /api/auth/refresh

Certificates:
  GET /api/certificates/
  POST /api/certificates/scan/
  GET /api/certificates/{id}/
  DELETE /api/certificates/{id}/

Alerts:
  GET /api/alerts/
  GET /api/alerts/stats/
  PATCH /api/alerts/{id}/acknowledge/

AD CS:
  GET /api/adcs-connectors/
  POST /api/adcs-connectors/
  POST /api/adcs-connectors/{id}/test/
  POST /api/adcs-connectors/{id}/sync/
  GET /api/internal-certificates/

Users:
  GET /api/users/
  POST /api/users/
  PUT /api/users/{id}/
  DELETE /api/users/{id}/
```

---

## 🚨 ALERTS SYSTEM

### Alert Generation

Alerts are automatically generated for:

**Certificate Expiry:**
- ✅ Expires < 7 days: CRITICAL alert
- ✅ Expires < 30 days: HIGH alert
- ✅ Expires < 90 days: MEDIUM alert

**Cryptographic Weakness:**
- ✅ Weak key length (< 2048 bits): HIGH alert
- ✅ Weak algorithm (MD5, SHA1): CRITICAL alert
- ✅ Self-signed certificates: MEDIUM alert

**Certificate Status:**
- ✅ Revoked certificates: CRITICAL alert
- ✅ Pending certificates: HIGH alert

### Alert Management

**Features:**
- Real-time alert dashboard
- Multi-criteria filtering
- Full-text search
- Severity-based sorting
- Expandable alert details
- Acknowledgment tracking
- Alert history and timeline

### Stats Cards Fix

**Issue:** Stats cards showing 0 for all severity levels

**Solution Implemented:**
1. Smart API response format detection
2. Fallback calculation from alerts array
3. Safe property access with nullish coalescing
4. Debug logging for troubleshooting

**Features:**
- Handles multiple API response formats
- Always displays accurate counts
- Shows loading state when needed
- No console errors

---

## 🔌 AD CS INTEGRATION

### How AD CS Manager Works

#### Connection Flow

```
1. Register AD CS Connector
   └─ Provide server address & credentials

2. Test Connection
   └─ Verify credentials work & access available

3. Sync Certificates
   └─ Query Windows CA for all certificates

4. Store Results
   └─ Save to database with metadata

5. Calculate Risks
   └─ Assess expiry & cryptography

6. Alert on Issues
   └─ Generate CRITICAL/HIGH/MEDIUM alerts

7. Display Results
   └─ Show in dashboard
```

#### Connection Methods

**Method 1: WinRM (Recommended)**
- Protocol: HTTP/HTTPS (port 5985/5986)
- Use: Windows environments with proper network access
- Implementation: PowerShell remoting
- Pros: Direct access, full cert details
- Cons: Requires WinRM enabled, port access

**Method 2: LDAP**
- Protocol: LDAP/LDAPS (port 389/636)
- Use: Any OS with LDAP access
- Implementation: LDAP queries
- Pros: Standard protocol, lightweight
- Cons: Limited details, user certs only

**Method 3: SSH**
- Protocol: SSH (port 22)
- Use: Firewalled environments
- Implementation: Remote script execution
- Pros: Works through firewalls
- Cons: Requires OpenSSH, custom scripts

#### Security Features

✅ **Credentials encrypted at rest**
✅ **Read-only access to Windows CA**
✅ **Full audit logging of all operations**
✅ **Role-based access control**
✅ **JWT authentication required**
✅ **Network-level security options**

### Using AD CS Connector

#### Step 1: Add Connector
```
POST /api/adcs-connectors/
{
  "name": "Production CA",
  "server_address": "ca.company.local",
  "port": 5985,
  "connection_type": "winrm",
  "username": "svc_certeye",
  "password": "SecurePassword123!",
  "domain": "COMPANY"
}
```

#### Step 2: Test Connection
```
POST /api/adcs-connectors/1/test/
Response: Connection successful ✅
```

#### Step 3: Sync Certificates
```
POST /api/adcs-connectors/1/sync/
Response: Discovered 342 certificates, imported 15
```

#### Step 4: View Results
```
GET /api/internal-certificates/
Shows all discovered certificates with risk scores
```

---

## 📊 DASHBOARD

### Dashboard Layout

```
┌─────────────────────────────────────┐
│  Summary Cards (4)                  │
│  ├─ Total Certificates              │
│  ├─ Expired Certificates            │
│  ├─ Expiring Soon                   │
│  └─ High Risk                       │
├─────────────────────────────────────┤
│  Charts                             │
│  ├─ Bar Chart: Expiry Distribution  │
│  └─ Pie Chart: Risk Distribution    │
├─────────────────────────────────────┤
│  Certificate Table                  │
│  ├─ Search by domain                │
│  ├─ Filter by risk level            │
│  └─ Sort options                    │
├─────────────────────────────────────┤
│  Recent Alerts                      │
│  └─ Last 5 alerts                   │
└─────────────────────────────────────┘
```

### Dashboard Features

**Real-time Statistics:**
- Total certificate count
- Expired certificates
- Certificates expiring within 30 days
- High-risk certificates (score > 60)

**Visual Charts:**
- Bar chart showing expiry distribution
- Pie chart showing risk distribution
- Color-coded by severity

**Certificate Inventory:**
- Domain name
- Issuer
- Risk score (0-100)
- Risk level (CRITICAL/HIGH/MEDIUM/LOW)
- Days until expiry
- Expiry date
- Search and filter

**Responsive Design:**
- Desktop: Full layout
- Tablet: Adapted layout
- Mobile: Single column, touch-friendly

---

## 🔐 SECURITY & AUDIT LOGGING

### Security Features

**Authentication:**
- ✅ JWT token-based
- ✅ Secure password hashing (bcrypt)
- ✅ Session management
- ✅ Token expiration

**Authorization:**
- ✅ Role-based access control (RBAC)
- ✅ Permission checking on all endpoints
- ✅ Resource-level permissions

**Data Protection:**
- ✅ Credentials encrypted at rest
- ✅ HTTPS/TLS for all communications
- ✅ SQL injection prevention
- ✅ CSRF protection

**Audit Trail:**
- ✅ All user actions logged
- ✅ Certificate changes tracked
- ✅ API access recorded
- ✅ Timestamps and user identification

### Audit Logging

**What's Logged:**
- User authentication events
- Certificate operations
- Alert acknowledgments
- Configuration changes
- User management actions
- AD CS sync operations
- API access patterns

**Retention:**
- 90 days by default
- Configurable retention policy
- Archive capability

---

## 📡 API REFERENCE

### Authentication Endpoints

```
POST /api/auth/login/
Body: { username, password }
Returns: { token, user_id, role }

POST /api/auth/logout/
Returns: { status: "success" }

POST /api/auth/refresh/
Returns: { token }
```

### Certificate Endpoints

```
GET /api/certificates/
Query params: ?risk_level=HIGH&days_to_expiry=30
Returns: [{ id, domain, issuer, risk_score, ... }]

POST /api/certificates/scan/
Body: { url }
Returns: { scan_id, status }

GET /api/certificates/{id}/
Returns: { Full certificate details }

DELETE /api/certificates/{id}/
Returns: { status: "deleted" }
```

### Alert Endpoints

```
GET /api/alerts/
Query params: ?severity=CRITICAL&status=pending
Returns: [{ id, message, severity, ... }]

GET /api/alerts/stats/
Returns: { CRITICAL: 5, HIGH: 8, MEDIUM: 3, LOW: 2 }

PATCH /api/alerts/{id}/acknowledge/
Returns: { status: "acknowledged" }
```

### AD CS Endpoints

```
POST /api/adcs-connectors/
Body: { name, server_address, connection_type, ... }
Returns: { id, status: "created" }

GET /api/adcs-connectors/
Returns: [{ All registered AD CS servers }]

POST /api/adcs-connectors/{id}/test/
Returns: { status: "success", connection_time_ms }

POST /api/adcs-connectors/{id}/sync/
Returns: { discovered: 342, imported: 15, ... }

GET /api/internal-certificates/
Returns: [{ All discovered certificates }]
```

---

## 🚀 DEPLOYMENT GUIDE

### System Requirements

**Server:**
- OS: Linux (Ubuntu 20.04+) or Windows Server 2019+
- RAM: 4GB minimum, 8GB recommended
- Disk: 50GB minimum (SSD recommended)
- Python: 3.8+
- Node.js: 16+

**External Services:**
- PostgreSQL: 12+
- Redis (optional, for caching)

### Installation Steps

#### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/sashen604/ISPMWEBCerteye.git
cd ISPMWEBCerteye

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
cd ssl_backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver 0.0.0.0:8001
```

#### 2. Frontend Setup

```bash
# Install dependencies
cd ssl_frontend
npm install

# Configure API endpoint
# Edit src/api.js with backend URL

# Start development server
npm run dev

# Build for production
npm run build
```

#### 3. Database Setup

```bash
# Create PostgreSQL database
createdb certeye

# Run migrations
python manage.py migrate

# Load fixtures (optional)
python manage.py loaddata fixtures/initial_data.json
```

### Production Deployment

**Security Checklist:**

- ✅ Set `DEBUG = False` in settings
- ✅ Configure `ALLOWED_HOSTS`
- ✅ Set strong `SECRET_KEY`
- ✅ Use HTTPS/TLS certificates
- ✅ Configure CORS properly
- ✅ Set up SSL for database connection
- ✅ Enable security headers
- ✅ Configure firewall rules
- ✅ Regular backup strategy
- ✅ Monitor logs and alerts

**Deployment Options:**

1. **Docker:**
   ```bash
   docker-compose up -d
   ```

2. **Manual Server:**
   - Set up gunicorn/uWSGI for backend
   - Configure nginx/Apache reverse proxy
   - Use systemd services for auto-start

3. **Cloud Platforms:**
   - AWS EC2/ECS
   - Azure App Service
   - Google Cloud Run
   - DigitalOcean

---

## 🔧 TROUBLESHOOTING

### Common Issues & Solutions

#### 1. Stats Cards Showing 0

**Problem:** Statistics cards display 0 for all severity levels

**Solution:**
- Check if alerts are loading (see "Alerts (X)" count)
- Open Developer Console (F12)
- Check for errors in Network tab
- Verify `/api/alerts/stats/` endpoint is working
- Check backend logs for errors

**Debug Command:**
```javascript
// In browser console
console.log('Check stats request in Network tab')
// Look for /api/alerts/stats/ response
```

#### 2. Alerts.map is not a function

**Problem:** Page crashes with "alerts.map is not a function"

**Solution:**
- Already fixed in latest version
- Add type checking before map:
  ```javascript
  {Array.isArray(alerts) && alerts.map(...)}
  ```

#### 3. AD CS Connection Fails

**Problem:** Cannot connect to AD CS server

**Solutions:**
- Verify server address is correct
- Check network connectivity to server
- Verify port is accessible (5985 for WinRM)
- Confirm credentials are correct
- Check firewall rules
- Test with `telnet server_address port`

#### 4. Certificate Scanning Not Working

**Problem:** Certificate scanning returns error

**Solutions:**
- Verify domain is accessible
- Check DNS resolution: `nslookup domain.com`
- Verify SSL/TLS is enabled
- Check firewall allows port 443
- Try manual scan first
- Check backend logs for details

#### 5. Database Connection Error

**Problem:** Cannot connect to PostgreSQL

**Solutions:**
- Verify PostgreSQL is running
- Check connection credentials in .env
- Verify database exists
- Check pg_hba.conf for authentication
- Verify firewall allows connection
- Test connection: `psql -U user -d certeye`

#### 6. Permission Denied Errors

**Problem:** Getting 403 Forbidden on certain endpoints

**Solutions:**
- Verify user role has permission
- Check token is valid
- Verify user not deactivated
- Check role-based permissions
- Try with admin account first

---

## 📚 QUICK START GUIDE

### First Time Setup

1. **Start Backend:**
   ```bash
   cd ssl_backend
   python manage.py runserver 8001
   ```

2. **Start Frontend:**
   ```bash
   cd ssl_frontend
   npm run dev
   ```

3. **Login:**
   - URL: `http://localhost:5174`
   - Username: `superadmin`
   - Password: `Admin@123456`

4. **Add First Certificate:**
   - Go to Dashboard → Scan Certificate
   - Enter domain: `google.com`
   - Wait for scan to complete

5. **View Results:**
   - See certificate details
   - Check risk score
   - View in dashboard

### Common Tasks

**Scan a Domain:**
```
Dashboard → Scan Certificate → Enter domain → Results
```

**Add AD CS Connector:**
```
Admin Panel → AD CS Connectors → Add New → Fill details → Test → Sync
```

**View Alerts:**
```
Alerts → Check severity cards → Use search/filters → Click to expand
```

**Export Certificates:**
```
Certificate List → Select items → Export (CSV/JSON)
```

---

## 📞 SUPPORT & RESOURCES

### Getting Help

- **Documentation:** Check README.md and this guide
- **Logs:** Check `/var/log/certeye/` for errors
- **API:** Test endpoints with curl or Postman
- **Database:** Use psql or pgAdmin for queries

### Useful Commands

```bash
# Check backend status
curl -X GET http://localhost:8001/api/certificates/

# Test authentication
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Admin@123456"}'

# View database
psql -d certeye -U certeye_user

# Check logs
tail -f /var/log/certeye/application.log
```

---

## ✅ FINAL STATUS

### Implementation Complete

✅ All features implemented
✅ All tests passed
✅ Documentation complete
✅ Security hardened
✅ Production ready

### Deployment Ready

✅ Code committed to GitHub
✅ Docker support available
✅ Environment templates provided
✅ Database migrations ready
✅ Backup strategy defined

### Support & Maintenance

✅ Comprehensive documentation
✅ Debug logging available
✅ Error handling in place
✅ Monitoring setup
✅ Update strategy planned

---

## 📅 VERSION HISTORY

| Version | Date | Status |
|---------|------|--------|
| 1.0 | April 19, 2026 | ✅ PRODUCTION READY |

---

**Project Status**: ✅ **COMPLETE AND OPERATIONAL**

For questions or issues, refer to the appropriate section above or check the GitHub repository.

---

*Last Updated: April 19, 2026*  
*Maintained by: CertEye Development Team*  
*Next Review: May 19, 2026*
