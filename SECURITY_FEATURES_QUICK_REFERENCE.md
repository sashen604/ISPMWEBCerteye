# Security Features Quick Reference

## 🛡️ Dark Mode
**Enable dark theme for easier viewing**
- Located in: Settings → Preferences
- Toggle: Dark Mode switch
- Persists: Across sessions via user profile

---

## 🔐 Authentication & Access

### Two-Factor Authentication (2FA)
**Require 2FA for all logins**
- **Location:** Settings → Security → Authentication & Access
- **Feature:** Toggle `Enable 2FA`
- **Process:**
  1. Click "Enable 2FA"
  2. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
  3. Enter 6-digit verification code
  4. Save backup codes in secure location
- **Disable:** Settings → Security → Enter password → Disable 2FA

### Login Notifications
**Get alerts when someone logs into your account**
- **Location:** Settings → Security → Authentication & Access
- **Feature:** Toggle `Enable Login Notifications`
- **Notification:** Email alert when new login detected
- **Default:** Enabled

### Suspicious Login Alerts
**Alert on logins from new locations or devices**
- **Location:** Settings → Security → Authentication & Access
- **Feature:** Toggle `Enable Suspicious Login Alerts`
- **Triggers:** New IP, new device/browser, geographic impossibility
- **Action:** Review alerts at Settings → Security → Suspicious Login Attempts
- **Default:** Enabled

### IP Whitelist
**Only allow logins from approved IP addresses**
- **Location:** Settings → Security → Authentication & Access
- **Feature:** Toggle `Enable IP Whitelist`
- **How to add IPs:**
  1. Enable IP Whitelist
  2. Go to Settings → Security → IP Whitelist
  3. Click "Add IP to Whitelist"
  4. Enter IP address and optional description
- **How to remove:** Click "Remove" next to IP in whitelist
- **Default:** Disabled

---

## ⏱️ Session & Password Policy

### Session Timeout
**Auto-logout after inactivity**
- **Location:** Settings → Security → Session & Password Policy
- **Value:** 15-480 minutes
- **Default:** 30 minutes
- **Effect:** User automatically logged out after specified inactivity

### Password Expiry
**Require password change**
- **Location:** Settings → Security → Session & Password Policy
- **Value:** 30-365 days
- **Default:** 90 days
- **Effect:** User prompted to change password after expiry

### API Key Rotation
**Rotate API keys periodically**
- **Location:** Settings → Security → Session & Password Policy
- **Value:** 30-365 days
- **Default:** 90 days
- **Recommended:** 90 days
- **Effect:** API keys automatically expire after specified period

---

## 🔑 API Keys

**API keys allow external applications to access the CertEye API**

### Generate New API Key
1. Settings → Security → API Keys
2. Click "Generate New API Key"
3. Enter name for the key
4. Copy and save both key and secret in secure location
5. **⚠️ WARNING:** Secret shown only once!

### View API Keys
- **Table shows:**
  - Key name
  - Creation date
  - Last used date
  - Status (active/revoked)

### Revoke API Key
1. Settings → Security → API Keys
2. Find the key to revoke
3. Click "Revoke" button
4. Confirm action
5. Key immediately disabled

### Security Best Practices
- Store secrets in secure vault (1Password, LastPass, etc.)
- Rotate keys every 90 days
- Revoke unused keys
- Never commit keys to version control
- Use scoped keys with minimum required permissions

---

## 👥 Active Sessions

**View and manage active user sessions**

### Current Session Details
- **Location:** Settings → Security → Active Sessions
- **Shows:**
  - Browser type (Chrome, Firefox, Safari, etc.)
  - Device type (Windows, Mac, iOS, etc.)
  - IP address
  - Last activity timestamp
  - Status badge (Active/Inactive)

### Sign Out Other Sessions
1. Settings → Security → Active Sessions
2. Click "Sign Out All Other Sessions"
3. Only current session remains active
4. All other devices logged out immediately

### Why This Matters
- Security: Logout from compromised devices
- Privacy: Remove old sessions from forgotten devices
- Management: Control where your account is accessed from

---

## 📋 Security Audit Log

**Track all security-related events**

### What's Logged
- Successful logins
- Failed login attempts
- Password changes
- 2FA enable/disable
- API key creation/revocation
- Settings changes
- Suspicious activities
- Account lock/unlock events

### How to View
1. Settings → Security → Security Audit Log
2. Shows last 10 events by default
3. Click "View all events" to see full history

### Event Details
- **Event type:** What happened
- **Timestamp:** When it happened
- **IP address:** Where from
- **Browser/Device:** What was used
- **Status:** Success/Failure/Warning

### Retention
- Events stored indefinitely
- Cannot be modified or deleted (compliance)
- Use for security investigations

---

## ⚠️ Suspicious Login Attempts

**Track and manage suspicious login attempts**

### What Triggers Alert
- Login from new IP address
- Login from new device/browser
- Geographic impossibility (e.g., New York then London in 5 minutes)
- Multiple failed login attempts from same IP
- Unusual time of day

### How to Review
1. Settings → Security → Suspicious Login Attempts
2. View list of flagged attempts
3. Review details: IP, location, device, browser

### Verify Legitimacy
1. Click on suspicious attempt
2. If it was you: Click "Mark as Verified"
3. If unauthorized: Click "Mark as Unauthorized" → Account locked
4. Contact admin if account compromised

### Actions Taken
- **Verified:** Attempt logged as legitimate, IP added to whitelist (optional)
- **Unverified:** Account temporarily locked, admin notified

---

## 📊 Comparison Table

| Feature | User Setting | Default | Impact |
|---------|--------------|---------|--------|
| 2FA | enable_2fa | OFF | Enhanced login security |
| Login Alerts | login_notifications | ON | Email notifications |
| Suspicious Alerts | suspicious_login_alerts | ON | Email & dashboard alerts |
| IP Whitelist | ip_whitelist_enabled | OFF | Restrict login locations |
| Session Timeout | session_timeout_minutes | 30 | Auto-logout on inactivity |
| Password Expiry | password_expiry_days | 90 | Force password change |
| API Key Rotation | api_key_rotation_days | 90 | Auto-expire API keys |
| Dark Mode | dark_mode | OFF | UI preference |

---

## 🔄 Common Workflows

### Secure Workstation Setup
1. Enable 2FA
2. Add workstation IP to whitelist
3. Set login notifications
4. Generate API key for integrations
5. Review audit logs monthly

### Away from Office
1. Disable IP whitelist (or whitelist mobile IP)
2. Enable suspicious login alerts
3. Check active sessions before leaving
4. Use strong password or 2FA

### Automated Process Setup
1. Generate API key with specific name
2. Save secret in secure vault
3. Configure rotation reminder
4. Monitor last_used date
5. Rotate key before expiry

### Emergency Account Compromise
1. Change password immediately
2. Enable 2FA if not already
3. Review active sessions → sign out all
4. Check audit logs for suspicious activity
5. Revoke all API keys
6. Contact administrator

---

## 🛠️ Administrator Tasks

### Set Security Policy
1. Admin Panel → User Settings
2. Configure default security settings
3. Enforce 2FA for admin accounts
4. Set session timeout globally
5. Review all user audit logs

### Investigate Security Incident
1. View User → Security Audit Log
2. Check suspicious login attempts
3. Review active sessions
4. Verify API key usage
5. Generate incident report

### User Account Recovery
1. Admin Panel → Reset User Password
2. User completes 2FA re-setup
3. Review and clear suspicious attempts
4. Issue new API keys if needed
5. Document incident

---

## 🚀 Quick Start Checklist

- [ ] Enable 2FA
- [ ] Review and verify login alerts
- [ ] Set appropriate session timeout
- [ ] Add trusted IPs to whitelist (if needed)
- [ ] Generate API keys for integrations
- [ ] Review security audit log
- [ ] Save backup codes (2FA)
- [ ] Set password expiry reminder
- [ ] Review active sessions monthly

---

## ❓ FAQ

**Q: What if I lose my 2FA device?**
A: Use backup codes. If lost, contact administrator to reset 2FA.

**Q: Can I have multiple API keys?**
A: Yes, generate as many as needed. One per integration recommended.

**Q: What happens when API key expires?**
A: Requests with expired key fail. Generate new key before expiry.

**Q: Is session timeout enforced automatically?**
A: Yes, user logged out after specified inactivity.

**Q: Can I export audit logs?**
A: Yes, contact administrator for export functionality.

**Q: What if I forget my password?**
A: Use forgot password link. 2FA may be required for verification.

**Q: How do I know if my account is compromised?**
A: Check suspicious login attempts and active sessions for unauthorized access.

**Q: Can I use IP whitelist with VPN?**
A: Yes, add your VPN's exit IP to whitelist.

---

## 📞 Support

For security issues:
1. Check this quick reference guide
2. Review audit logs and active sessions
3. Contact your system administrator
4. Never share passwords or API keys with support
5. Use secure password manager for credentials

---

**Last Updated:** April 19, 2026  
**Version:** 1.0
