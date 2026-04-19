# Audit Logging System - Implementation Complete

## Overview

Comprehensive audit logging system for recording all important actions across the CertEye platform for accountability, security, and compliance.

## ✅ Completed Implementation

### Database Models

**AuditLog** - Generic audit events
- Fields: user, action, target_type, target_id, details, ip_address, created_at
- Actions: login, logout, certificate_create, certificate_delete, role_change, alert_create, etc.
- Indexes: user + created_at, action + created_at, target_type + target_id

**CertificateAuditLog** - Certificate operations
- Fields: user, action, certificate_id, certificate_name, domain, old_values, new_values, ip_address, timestamp
- Actions: create, update, delete, scan, import
- Indexes: user + timestamp, action + timestamp, certificate_id

**AlertAuditLog** - Alert operations
- Fields: user, action, alert_id, alert_type, certificate_id, certificate_name, old_values, new_values, ip_address, timestamp
- Actions: create, update, resolve, reopen, dismiss
- Indexes: user + timestamp, action + timestamp, alert_id, certificate_id

### Centralized Service

**AuditLoggingService** (`apps/audit_logs/services.py`)

Methods:
- `get_client_ip(request)` - Extract IP from X-Forwarded-For or REMOTE_ADDR
- `log_action()` - Generic action logging
- `log_certificate_action()` - Certificate create/update/delete/scan logging
- `log_alert_action()` - Alert operation logging
- `log_login()` - User login events
- `log_logout()` - User logout events
- `log_role_change()` - User role changes
- `log_risk_config_update()` - Risk configuration updates

### API Endpoints

All endpoints require SuperAdmin or Admin role.

**General Audit Logs**
```
GET /api/audit/
Query Parameters:
  - action: Filter by action
  - user_id: Filter by user ID
  - target_type: Filter by target type
  - date_from: From date (YYYY-MM-DD)
  - date_to: To date (YYYY-MM-DD)
  - page: Page number (default: 1)
  - limit: Results per page (default: 50, max: 500)

Response:
{
  "success": true,
  "total": 100,
  "page": 1,
  "limit": 50,
  "pages": 2,
  "data": [...]
}
```

**Certificate Audit Logs**
```
GET /api/audit/certificates/
Query Parameters:
  - action: create|update|delete|scan|import
  - certificate_id: Filter by certificate ID
  - user_id: Filter by user ID
  - date_from/date_to: Date range
  - page/limit: Pagination
```

**Alert Audit Logs**
```
GET /api/audit/alerts/
Query Parameters:
  - action: create|update|resolve|reopen|dismiss
  - alert_id: Filter by alert ID
  - certificate_id: Filter by certificate ID
  - user_id: Filter by user ID
  - date_from/date_to: Date range
  - page/limit: Pagination
```

### Logging Integration

**Certificate Operations**
- ✅ Certificate scan - logs with IP, user, timestamp, new cert values
- ✅ Certificate update - logs old vs new risk levels, issuer, expiry
- ✅ Certificate delete - logs full certificate data before deletion
- ✅ IP address automatically captured from request

**Existing Logging (Already Working)**
- ✅ User login/logout - tracked via UserLoginLog model
- ✅ User registration - tracked via UserRegistrationLog model
- ✅ Role changes - tracked via UserAuditLog model
- ✅ User deletion - tracked via UserAuditLog model

### Usage Examples

**Test Certificate Scan Logging**
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Admin@123456"}' \
  | jq -r '.access')

# Scan a domain (creates audit log)
curl -X POST http://localhost:8001/api/certificates/scan/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'

# View certificate audit logs
curl -X GET "http://localhost:8001/api/audit/certificates/" \
  -H "Authorization: Bearer $TOKEN"

# Filter by action
curl -X GET "http://localhost:8001/api/audit/certificates/?action=update" \
  -H "Authorization: Bearer $TOKEN"

# Filter by date range
curl -X GET "http://localhost:8001/api/audit/?date_from=2026-04-19&date_to=2026-04-20" \
  -H "Authorization: Bearer $TOKEN"
```

## Data Captured

### Certificate Operations
```json
{
  "action": "update",
  "user": "superadmin",
  "certificate_id": 3,
  "certificate_name": "CN=*.example.com",
  "domain": "example.com",
  "new_values": {
    "issuer": "CN=DigiCert...",
    "valid_to": "2027-01-23 23:59:59",
    "risk_level": "LOW"
  },
  "ip_address": "192.168.1.1",
  "timestamp": "2026-04-19T10:27:23.120101Z"
}
```

### User Actions
```json
{
  "action": "role_change",
  "user": "superadmin",
  "target_username": "john_doe",
  "old_role": "user",
  "new_role": "admin",
  "ip_address": "192.168.1.1",
  "timestamp": "2026-04-19T10:27:23.120101Z"
}
```

## Database Migration

```bash
# Apply all pending migrations
python manage.py migrate

# Migrations applied:
# - audit_logs.0001_initial - Initial AuditLog model
# - audit_logs.0002_enhanced_audit_logs - CertificateAuditLog and AlertAuditLog
# - audit_logs.0003_rename_metadata_to_details - Field rename
```

## Security Features

1. **Access Control** - Only SuperAdmin and Admin can view audit logs
2. **IP Tracking** - Client IP captured from each action
3. **User Identification** - All actions linked to authenticated user
4. **Immutability** - Audit logs are append-only (no update/delete)
5. **Detailed Logging** - Old and new values stored for compliance
6. **Timestamp** - Precise timestamp for each action

## Performance

- Database indexes on frequently filtered columns
- Pagination to prevent memory overload
- Efficient JSON field queries
- Connection pooling recommended for production

## Future Enhancements

1. **Alert Logging** - Add logging to alert create/update/resolve operations
2. **Frontend UI** - Create audit logs page with filters and export
3. **Retention Policy** - Archive logs after N days
4. **Search** - Full-text search across audit logs
5. **Async Logging** - Queue logging via Celery for high-volume scenarios
6. **Log Analysis** - Generate security reports and anomaly detection

## Testing

All audit logging is production-ready and tested with:
- ✅ Certificate scan operations
- ✅ User and IP address capture
- ✅ Filtering and pagination
- ✅ JSON details storage
- ✅ Permission checks

## Files Modified/Created

- ✅ `apps/audit_logs/models.py` - Enhanced audit models
- ✅ `apps/audit_logs/services.py` - Audit logging service
- ✅ `apps/audit_logs/serializers.py` - API serializers
- ✅ `apps/audit_logs/views.py` - API endpoints
- ✅ `apps/audit_logs/urls.py` - URL routing
- ✅ `apps/audit_logs/migrations/0002_enhanced_audit_logs.py` - Schema migration
- ✅ `apps/audit_logs/migrations/0003_rename_metadata_to_details.py` - Field rename
- ✅ `apps/certificates/services.py` - Certificate logging integration
- ✅ `apps/certificates/views.py` - Certificate scan/delete logging

---

**Status:** Production Ready ✅
**Verified:** 2026-04-19
**Coverage:** Certificate operations, user actions, timestamps, IPs
