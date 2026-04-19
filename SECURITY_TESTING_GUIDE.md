# Security Features Testing Guide

## Test Environment Setup

### Prerequisites
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000 (or configured URL)
- Test user with superadmin role
- Postman or similar API testing tool (optional)

### Test Credentials
```
Username: superadmin
Password: Admin@123456
Email: admin@certeye.local
```

---

## API Testing

### 1. Authentication & Token

#### Test 1.1: Obtain Access Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Admin@123456"}'

# Expected response:
{
  "success": true,
  "user": {...},
  "access": "eyJ0...",
  "refresh": "eyJ0..."
}
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 1.2: Use Access Token
```bash
TOKEN="<access_token_from_test_1.1>"

curl -X GET http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with user data
```

**Status:** ✅ PASS / ❌ FAIL

---

### 2. Security Settings

#### Test 2.1: Get Current Security Settings
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/settings \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response includes all security fields with default values
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 2.2: Update Security Settings
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_2fa": false,
    "login_notifications": true,
    "suspicious_login_alerts": true,
    "ip_whitelist_enabled": false,
    "session_timeout_minutes": 45,
    "password_expiry_days": 60,
    "api_key_rotation_days": 90,
    "dark_mode": true
  }'

# Expected: 200 OK with updated settings
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 2.3: Verify Settings Persisted
```bash
# Run Test 2.1 again
# Verify dark_mode is now true
```

**Status:** ✅ PASS / ❌ FAIL

---

### 3. API Keys

#### Test 3.1: List API Keys (empty initially)
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/api-keys \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "api_keys": [] }
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 3.2: Generate New API Key
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test API Key"}'

# Expected: 201 Created
# Response includes: id, key, secret, created_at
# Save the key and secret for later tests
```

**Status:** ✅ PASS / ❌ FAIL
**API Key ID:** ____________
**API Key:** ________________
**API Secret:** ________________

#### Test 3.3: List API Keys (should show 1)
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/api-keys \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "api_keys": [{ ... }] }
# Count should be 1
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 3.4: Revoke API Key
```bash
TOKEN="<access_token>"
KEY_ID="<id_from_test_3.2>"

curl -X DELETE http://localhost:8000/api/auth/security/api-keys/$KEY_ID/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "message": "API key revoked" }
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 3.5: Verify Key Revoked
```bash
# Run Test 3.3 again
# Should show is_active: false for revoked key
```

**Status:** ✅ PASS / ❌ FAIL

---

### 4. IP Whitelist

#### Test 4.1: List Whitelisted IPs (empty initially)
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/ip-whitelist \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "ips": [] }
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 4.2: Add IP to Whitelist
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/ip-whitelist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.1.100",
    "description": "Office network"
  }'

# Expected: 201 Created
# Response includes id, ip_address, description, created_at
```

**Status:** ✅ PASS / ❌ FAIL
**IP Whitelist ID:** ____________

#### Test 4.3: List Whitelisted IPs (should show 1)
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/ip-whitelist \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with 1 IP
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 4.4: Remove IP from Whitelist
```bash
TOKEN="<access_token>"
IP_ID="<id_from_test_4.2>"

curl -X DELETE http://localhost:8000/api/auth/security/ip-whitelist/$IP_ID/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "message": "IP removed..." }
```

**Status:** ✅ PASS / ❌ FAIL

---

### 5. Active Sessions

#### Test 5.1: List Active Sessions
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/sessions \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Should show at least current session
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 5.2: Sign Out All Other Sessions
```bash
TOKEN="<access_token>"

curl -X DELETE http://localhost:8000/api/auth/security/sessions \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response: { "success": true, "message": "Signed out..." }
```

**Status:** ✅ PASS / ❌ FAIL

---

### 6. Security Audit Logs

#### Test 6.1: Get Security Audit Logs
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/audit-logs \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Should show events from previous tests
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 6.2: Verify Event Types in Logs
```bash
# From Test 6.1, verify events include:
# - settings_changed (from Test 2.2)
# - api_key_created (from Test 3.2)
# - api_key_revoked (from Test 3.4)
# - ip_whitelisted (from Test 4.2)
# - session_terminated (from Test 5.2)
```

**Status:** ✅ PASS / ❌ FAIL

---

### 7. Suspicious Login Attempts

#### Test 7.1: List Suspicious Attempts
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/suspicious-attempts \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# May be empty initially
```

**Status:** ✅ PASS / ❌ FAIL

---

### 8. Two-Factor Authentication

#### Test 8.1: Get 2FA Secret
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/2fa/enable \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Response includes: secret, qr_code URL
```

**Status:** ✅ PASS / ❌ FAIL
**2FA Secret:** ________________

#### Test 8.2: Verify 2FA Activation
```bash
TOKEN="<access_token>"
SECRET="<secret_from_test_8.1>"

curl -X PUT http://localhost:8000/api/auth/security/2fa/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "'$SECRET'",
    "verification_code": "123456"
  }'

# Expected: 200 OK
# Response includes: backup_codes array
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 8.3: Verify Settings Show 2FA Enabled
```bash
TOKEN="<access_token>"

curl -X GET http://localhost:8000/api/auth/security/settings \
  -H "Authorization: Bearer $TOKEN"

# Expected: enable_2fa should be true
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 8.4: Disable 2FA
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/2fa/disable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"Admin@123456"}'

# Expected: 200 OK
# Response: { "success": true, "message": "2FA disabled..." }
```

**Status:** ✅ PASS / ❌ FAIL

#### Test 8.5: Disable 2FA with Wrong Password
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/2fa/disable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"WrongPassword"}'

# Expected: 401 Unauthorized
# Response: { "success": false, "error": "Invalid password" }
```

**Status:** ✅ PASS / ❌ FAIL

---

## Frontend Testing

### Settings Page Navigation

#### Test F1: Access Settings Page
1. Login to application
2. Navigate to Settings or click user menu
3. Select "⚙️ Settings"

**Expected:** Settings page loads with tabs
**Status:** ✅ PASS / ❌ FAIL

#### Test F2: Profile Tab
1. Click "👤 Profile" tab
2. Verify fields: Username, Email, First Name, Last Name, Role, Member Since
3. Edit email address
4. Click "💾 Save Changes"
5. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F3: Password Tab
1. Click "🔐 Password" tab
2. Enter current password
3. Enter new password (8+ chars)
4. Confirm password
5. Click "🔄 Change Password"
6. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F4: Preferences Tab
1. Click "🎨 Preferences" tab
2. Toggle "Dark Mode"
3. Verify theme changes
4. Adjust "Alert Threshold" value
5. Select different "Items Per Page"
6. Click "💾 Save Preferences"
7. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F5: Notifications Tab
1. Click "🔔 Notifications" tab
2. Toggle "Email Alerts"
3. Toggle "Dashboard Alerts"
4. Enter notification email
5. Click "💾 Save Notification Settings"
6. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F6: Security Tab - Authentication
1. Click "🛡️ Security" tab
2. Verify 4 toggles present:
   - 2FA
   - Login Notifications
   - Suspicious Login Alerts
   - IP Whitelist
3. Toggle each one
4. Click "💾 Save Security Settings"
5. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F7: Security Tab - Policies
1. Update "Session Timeout" to 45 minutes
2. Update "Password Expiry" to 60 days
3. Update "API Key Rotation" to 90 days
4. Click "💾 Save Security Settings"
5. Reload page
6. Verify values persisted

**Status:** ✅ PASS / ❌ FAIL

#### Test F8: Security Tab - API Keys
1. Click "Generate New API Key"
2. Enter name: "Test Key"
3. Verify key and secret displayed
4. Copy and save key
5. Verify key appears in table
6. Click "Revoke"
7. Confirm action
8. Verify status changed to "revoked"

**Status:** ✅ PASS / ❌ FAIL

#### Test F9: Security Tab - Active Sessions
1. View "Current Session" details
2. Verify browser, device, IP shown
3. Click "Sign Out All Other Sessions"
4. Verify confirmation
5. Verify success message

**Status:** ✅ PASS / ❌ FAIL

#### Test F10: Security Tab - Audit Log
1. View "Security Audit Log" table
2. Verify events from previous tests listed
3. Verify timestamps, status, event type visible
4. Click "View all events" link
5. Verify full history loads

**Status:** ✅ PASS / ❌ FAIL

---

## Responsive Design Testing

### Mobile (375px width)
- [ ] Settings tabs display as buttons
- [ ] Forms stack vertically
- [ ] Tables display on mobile
- [ ] Buttons clickable
- [ ] Text readable

**Status:** ✅ PASS / ❌ FAIL

### Tablet (768px width)
- [ ] Two-column layout works
- [ ] Forms readable
- [ ] Tables formatted correctly
- [ ] Spacing appropriate

**Status:** ✅ PASS / ❌ FAIL

### Desktop (1200px width)
- [ ] Full layout working
- [ ] All features visible
- [ ] Professional appearance

**Status:** ✅ PASS / ❌ FAIL

---

## Error Handling Testing

#### Test E1: Unauthorized Access
```bash
# Try to access security settings without token
curl -X GET http://localhost:8000/api/auth/security/settings

# Expected: 401 Unauthorized
```

**Status:** ✅ PASS / ❌ FAIL

#### Test E2: Invalid Token
```bash
curl -X GET http://localhost:8000/api/auth/security/settings \
  -H "Authorization: Bearer invalid_token"

# Expected: 401 Unauthorized
```

**Status:** ✅ PASS / ❌ FAIL

#### Test E3: Resource Not Found
```bash
TOKEN="<access_token>"

curl -X DELETE http://localhost:8000/api/auth/security/api-keys/99999/ \
  -H "Authorization: Bearer $TOKEN"

# Expected: 404 Not Found
```

**Status:** ✅ PASS / ❌ FAIL

#### Test E4: Invalid Data
```bash
TOKEN="<access_token>"

curl -X POST http://localhost:8000/api/auth/security/ip-whitelist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "invalid_ip"}'

# Expected: 400 Bad Request
```

**Status:** ✅ PASS / ❌ FAIL

---

## Performance Testing

#### Test P1: API Response Time
```bash
TOKEN="<access_token>"

time curl -X GET http://localhost:8000/api/auth/security/settings \
  -H "Authorization: Bearer $TOKEN"

# Target: <100ms
# Actual: ___ms
```

**Status:** ✅ PASS / ❌ FAIL

#### Test P2: Audit Log Query (Large Dataset)
```bash
TOKEN="<access_token>"

time curl -X GET http://localhost:8000/api/auth/security/audit-logs?limit=1000 \
  -H "Authorization: Bearer $TOKEN"

# Target: <500ms
# Actual: ___ms
```

**Status:** ✅ PASS / ❌ FAIL

#### Test P3: Frontend Page Load
1. Open Settings page in browser
2. Check page load time (DevTools Network tab)
3. Target: <2 seconds
4. Actual: ___ms

**Status:** ✅ PASS / ❌ FAIL

---

## Security Testing

#### Test S1: API Key Secret Visibility
1. Generate API key
2. Note secret value
3. Refresh page
4. List API keys
5. Verify secret NOT visible in list

**Status:** ✅ PASS / ❌ FAIL

#### Test S2: Password Confirmation
1. Attempt to disable 2FA
2. Try without password
3. Expected: Error message
4. Enter wrong password
5. Expected: Unauthorized error

**Status:** ✅ PASS / ❌ FAIL

#### Test S3: Session Token Handling
1. Logout from one browser tab
2. Try API call in another tab
3. Expected: 401 Unauthorized

**Status:** ✅ PASS / ❌ FAIL

---

## Data Validation Testing

#### Test D1: Field Constraints
- Session Timeout: Min 15, Max 480
- Password Expiry: Min 30, Max 365
- API Key Rotation: Min 30, Max 365

Verify:
- [ ] Values below minimum rejected
- [ ] Values above maximum rejected
- [ ] Valid values accepted
- [ ] Non-numeric values rejected

**Status:** ✅ PASS / ❌ FAIL

#### Test D2: Duplicate Prevention
1. Add IP "192.168.1.1" to whitelist
2. Try to add same IP again
3. Expected: Success (updated) or error (duplicate)

**Status:** ✅ PASS / ❌ FAIL

---

## Database Integrity Testing

#### Test DB1: Migration Applied
```bash
python manage.py showmigrations authentication
# Verify 0005 shows [X]
```

**Status:** ✅ PASS / ❌ FAIL

#### Test DB2: Tables Created
```bash
python manage.py dbshell
# SELECT name FROM sqlite_master WHERE type='table';
# Verify: APIKey, IPWhitelist, UserSession, SecurityAuditLog, SuspiciousLoginAttempt
```

**Status:** ✅ PASS / ❌ FAIL

#### Test DB3: User Fields Updated
```bash
python manage.py dbshell
# Describe authentication_user;
# Verify all 12 new fields present
```

**Status:** ✅ PASS / ❌ FAIL

---

## Test Summary

### Total Tests: 60+
- API Tests: 25
- Frontend Tests: 10
- Responsive Tests: 3
- Error Handling: 5
- Performance: 3
- Security: 3
- Data Validation: 2
- Database: 3

### Overall Status
- **Passed:** ___ / ___
- **Failed:** ___ / ___
- **Success Rate:** ___%

---

## Sign-Off

### QA Lead
Name: _________________ Date: _______
Status: ✅ PASS / ⚠️ CONDITIONAL / ❌ FAIL

### Comments/Issues Found:
```
[Space for test results and notes]
```

---

## Known Issues Logged

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| [Issue 1] | High/Med/Low | Open/Closed | [Description] |
| | | | |

---

**Test Execution Date:** April 19, 2026  
**Test Version:** 1.0  
**Tested By:** ________________
