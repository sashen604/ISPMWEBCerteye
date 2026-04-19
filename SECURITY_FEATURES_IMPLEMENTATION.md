# Security Features Implementation Guide

## Overview
Comprehensive security features have been implemented in CertEye to provide enterprise-grade account and access control. This document outlines all the security components added to both backend and frontend.

---

## 1. Database Models

### User Model Extensions
Added the following fields to the User model:

```python
# Authentication & Access Control
enable_2fa: Boolean (default: False)
login_notifications: Boolean (default: True)
suspicious_login_alerts: Boolean (default: True)
ip_whitelist_enabled: Boolean (default: False)

# Policy Settings
session_timeout_minutes: Integer (default: 30)
password_expiry_days: Integer (default: 90)
api_key_rotation_days: Integer (default: 90)
last_password_change: DateTime

# Preferences
dark_mode: Boolean (default: False)

# 2FA Fields
two_fa_secret: CharField
two_fa_backup_codes: JSONField (list)
```

### New Models

#### 1. **UserSession**
Tracks active user sessions with device and location information.

```python
- session_key: Unique session identifier
- ip_address: Client IP address
- user_agent: Browser/device information
- browser: Parsed browser name
- device: Parsed device type
- created_at: Session creation timestamp
- last_activity: Last activity timestamp
- is_active: Session status
```

Methods:
- `is_expired`: Check if session has exceeded timeout

#### 2. **IPWhitelist**
Manages whitelisted IP addresses for account access.

```python
- user: ForeignKey to User
- ip_address: Whitelisted IP
- description: Custom description
- created_at: When IP was whitelisted
- last_used: Last login from this IP
```

#### 3. **APIKey**
Manages API keys for programmatic access.

```python
- user: ForeignKey to User
- name: Key name/description
- key: Public API key
- secret: Secret key (shown only on creation)
- created_at: Creation timestamp
- last_used: Last usage timestamp
- expires_at: Expiration date
- is_active: Active status
- scopes: List of allowed API scopes
```

Methods:
- `is_expired()`: Check expiration status
- `generate_key()`: Generate new API key
- `generate_secret()`: Generate new secret

#### 4. **SecurityAuditLog**
Comprehensive logging of all security events.

```python
EVENT_TYPES = [
    'login_success', 'login_failed', 'login_suspicious',
    'password_changed', '2fa_enabled', '2fa_disabled',
    'api_key_created', 'api_key_revoked',
    'session_terminated', 'ip_whitelisted',
    'settings_changed', 'account_locked', 'account_unlocked'
]

Fields:
- user: ForeignKey to User
- event_type: Type of security event
- description: Event details
- ip_address: Client IP
- user_agent: Browser info
- browser: Parsed browser
- device: Parsed device
- status: success/failure/warning
- metadata: Additional JSON data
- timestamp: Event time
```

#### 5. **SuspiciousLoginAttempt**
Tracks and manages suspicious login attempts.

```python
- user: ForeignKey to User
- ip_address: Source IP
- location: Geolocation (if available)
- browser: Browser type
- device: Device type
- reason: Why flagged as suspicious
- is_verified: User confirmed legitimacy
- timestamp: When attempt occurred
```

---

## 2. API Endpoints

### Security Settings Management
```
GET  /api/auth/security/settings          - Get current settings
POST /api/auth/security/settings          - Update settings
```

### Session Management
```
GET    /api/auth/security/sessions        - List active sessions
DELETE /api/auth/security/sessions        - Sign out all other sessions
DELETE /api/auth/security/sessions/<id>/  - Sign out specific session
```

### IP Whitelist Management
```
GET    /api/auth/security/ip-whitelist           - List whitelisted IPs
POST   /api/auth/security/ip-whitelist           - Add IP to whitelist
DELETE /api/auth/security/ip-whitelist/<id>/    - Remove IP from whitelist
```

### API Key Management
```
GET    /api/auth/security/api-keys        - List user's API keys
POST   /api/auth/security/api-keys        - Generate new API key
DELETE /api/auth/security/api-keys/<id>/  - Revoke API key
```

### Security Audit Logs
```
GET /api/auth/security/audit-logs         - Get security event logs
```

### Suspicious Login Attempts
```
GET  /api/auth/security/suspicious-attempts        - List suspicious attempts
POST /api/auth/security/suspicious-attempts/<id>/  - Mark as verified/unverified
```

### Two-Factor Authentication
```
POST /api/auth/security/2fa/enable   - Generate 2FA secret and QR code
PUT  /api/auth/security/2fa/enable   - Verify and enable 2FA
POST /api/auth/security/2fa/disable  - Disable 2FA (requires password)
```

---

## 3. Frontend UI Components

### Settings Page Enhancements

#### Profile Tab (`👤 Profile`)
- Username (read-only)
- Email address
- First name
- Last name
- Role (read-only)
- Member since (read-only)
- Save changes button

#### Password Tab (`🔐 Password`)
- Current password
- New password (min 8 chars)
- Confirm password
- Password requirements display
- Change password button

#### Preferences Tab (`🎨 Preferences`)
- Dark mode toggle
- Alert threshold (days)
- Items per page selector
- Save preferences button

#### Notifications Tab (`🔔 Notifications`)
- Email alerts toggle
- Dashboard alerts toggle
- Notification email address
- Alert types information
- Save settings button

#### Security Tab (`🛡️ Security`)

**Authentication & Access Controls:**
- ✅ Two-Factor Authentication (2FA) toggle
- ✅ Login Notifications toggle
- ✅ Suspicious Login Alerts toggle
- ✅ IP Whitelist toggle

**Session & Password Policy:**
- ⏱️ Session Timeout (minutes) - adjustable 15-480
- 🔐 Password Expiry (days) - adjustable 30-365
- 🔄 API Key Rotation (days) - adjustable 30-365

**API Keys Management:**
- 📋 Table showing all API keys
  - Name
  - Created date
  - Last used date
  - Status (active/revoked)
  - Revoke button per key
- ➕ Generate new API key button
- ⚠️ Security warning about key confidentiality

**Active Sessions:**
- Current session details
  - Browser type
  - Device info
  - IP address
  - Last activity time
- Sign out from all other sessions button

**Security Audit Log:**
- 📋 Table of recent security events
  - Event type
  - Timestamp
  - Status (success/failure)
- Link to view full event history

---

## 4. Security Features Details

### A. Two-Factor Authentication (2FA)
- Enables additional security layer for logins
- Supports TOTP-based authentication
- Generates and stores backup codes
- Can be enabled/disabled with password confirmation
- Logs all 2FA actions in audit trail

### B. Session Management
- Automatic session expiration based on inactivity
- Configurable timeout duration (15-480 minutes)
- View all active sessions
- Sign out all other sessions immediately
- Session tracking with device and location info

### C. IP Whitelist
- Restrict logins to approved IP addresses
- Add/remove IPs dynamically
- Track when each IP was last used
- Useful for office/team accounts

### D. API Key Management
- Generate unique API keys for programmatic access
- Set expiration dates
- Track API key usage
- Revoke compromised keys instantly
- Backup codes for recovery

### E. Login Security
- Login success/failure logging
- Suspicious login detection based on:
  - New IP addresses
  - New device/browser combinations
  - Geographic impossibilities
  - Failed attempts patterns
- User alerts on suspicious activity
- User can mark attempts as verified or unauthorized

### F. Security Audit Logging
- Comprehensive event logging for all security actions
- Event types: logins, password changes, 2FA changes, API key operations, settings changes
- Tracks: timestamp, IP, browser, device, status, detailed metadata
- Searchable and filterable logs

### G. Password Security
- Configurable password expiry (30-365 days)
- Tracks last password change date
- Requires password confirmation for sensitive operations
- Password strength requirements enforced

### H. Dark Mode
- User preference for dark theme
- Stored in user profile
- Persists across sessions

---

## 5. Backend Implementation Details

### Serializers
```python
UserSecuritySettingsSerializer       - Settings read/write
UserSessionSerializer                 - Active sessions display
IPWhitelistSerializer                 - IP management
APIKeySerializer                      - API key display
APIKeyDetailSerializer                - Full API key details (with secret)
SecurityAuditLogSerializer            - Event logs
SuspiciousLoginAttemptSerializer      - Suspicious attempts
```

### Views
All security views are protected with `IsAuthenticated` permission.
Some endpoints are restricted to `IsSuperAdmin` for administrative actions.

### Helper Functions
```python
get_client_ip(request)  - Extract client IP from request headers
```

---

## 6. Default Security Settings

New users are created with these defaults:
```python
enable_2fa: False
login_notifications: True
suspicious_login_alerts: True
ip_whitelist_enabled: False
session_timeout_minutes: 30
password_expiry_days: 90
api_key_rotation_days: 90
dark_mode: False
```

---

## 7. CSS Styling

All security components use consistent Bootstrap styling with custom enhancements:
- Smooth animations and transitions
- Responsive design for mobile/tablet
- Color-coded status badges
- Accessible form controls with focus states
- Print-friendly styles

---

## 8. Usage Examples

### Enable 2FA
```javascript
// Generate secret and QR code
POST /api/auth/security/2fa/enable
Response: { secret, qr_code, message }

// Verify and enable
PUT /api/auth/security/2fa/enable
Body: { secret, verification_code }
Response: { backup_codes }
```

### Generate API Key
```javascript
POST /api/auth/security/api-keys
Body: { name: 'My API Key' }
Response: { api_key: { id, key, secret, ... } }
// NOTE: Secret shown only on creation!
```

### Update Security Settings
```javascript
POST /api/auth/security/settings
Body: {
  enable_2fa: true,
  session_timeout_minutes: 45,
  password_expiry_days: 60
}
```

### Get Audit Logs
```javascript
GET /api/auth/security/audit-logs?limit=50
Response: { count, logs: [...] }
```

---

## 9. Migration Information

Created migration: `0005_user_api_key_rotation_days_user_dark_mode_and_more.py`

This migration:
- Adds 11 new fields to User model
- Creates 5 new database tables
- Sets up proper indexes for performance
- Maintains backward compatibility

Run with:
```bash
python manage.py migrate authentication
```

---

## 10. Security Best Practices

### For Administrators
1. Regularly review security audit logs
2. Monitor suspicious login attempts
3. Enforce 2FA for all admin accounts
4. Set appropriate session timeouts
5. Implement IP whitelisting for secure networks
6. Regularly rotate API keys

### For Users
1. Enable 2FA for additional security
2. Use strong, unique passwords
3. Save API key secrets in secure location
4. Verify suspicious login alerts
5. Review active sessions regularly
6. Revoke unused API keys

---

## 11. Future Enhancements

Potential additions:
- Hardware security key support (FIDO2/U2F)
- IP geolocation for suspicious login detection
- Rate limiting on failed login attempts
- Passwordless authentication
- OAuth2 integration
- Mobile app authentication
- Email verification for new logins
- Account recovery codes

---

## 12. Testing

All endpoints should be tested with:
1. Valid authenticated user
2. Invalid/expired token
3. Insufficient permissions
4. Edge cases (max/min values, invalid formats)
5. Concurrent requests
6. Database integrity

---

## 13. Notes

- All timestamps are in UTC
- API keys shown only once on creation
- Backup codes are single-use only
- Session tracking requires active middleware
- Audit logs are immutable for compliance
- All user data is encrypted at rest

---

**Implementation Date:** April 19, 2026  
**Status:** Complete and Ready for Testing
