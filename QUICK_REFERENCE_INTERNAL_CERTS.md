# Internal Certificate Collection - Quick Reference Card

## 🚀 Quick Start (5 minutes)

```bash
# 1. Create migrations and apply
cd ssl_backend
python manage.py makemigrations
python manage.py migrate

# 2. Generate agent token
python manage.py shell
from apps.certificates.agent_auth import AgentAuthenticator
token = AgentAuthenticator().generate_token('MyAgent', 'SERVER01')
print(token)  # Copy this token!
exit()

# 3. Run tests
python apps/certificates/test_internal_certs.py "your_token_here"

# 4. Start frontend
cd ../ssl_frontend
npm run dev
# Navigate to: http://localhost:5173 → "Internal Certificates"
```

---

## 📡 API Endpoints at a Glance

### 1. Submit Certificate
```bash
POST /api/certificates/collect/

# Single
{
  "agent_token": "abc...",
  "hostname": "SERVER01",
  "subject": "server.example.com",
  "issuer": "CA",
  "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
  "valid_to": "2025-12-31T23:59:59Z"
}

# Batch
{
  "agent_token": "abc...",
  "certificates": [
    { ...cert1... },
    { ...cert2... }
  ]
}

Response: 200/201 + {success, message, certificate}
```

### 2. List Certificates
```bash
GET /api/certificates/?source_type=internal_agent&hostname=SERVER01
# Auth: JWT token required

Response: {count, results: [certificates]}
```

### 3. Agent Status
```bash
GET /api/certificates/agent_status/
# Auth: JWT token required

Response: {agents: [...], summary: {...}}
```

---

## 🔑 Code Reference

### Generate Token
```python
from apps.certificates.agent_auth import AgentAuthenticator
auth = AgentAuthenticator()
token = auth.generate_token('Agent-Name', 'HOSTNAME')
```

### Ingest Certificate
```python
from apps.certificates.internal_service import InternalCertificateService

service = InternalCertificateService()
result = service.ingest_certificate({
    'subject': '...',
    'issuer': '...',
    'thumbprint': '...',
    'hostname': '...',
    'valid_to': '2025-12-31...'
}, agent_id='...')

print(result['success'])  # True/False
print(result['certificate'].risk_level)  # CRITICAL/HIGH/MEDIUM/LOW
```

### Check Rate Limit
```python
from apps.certificates.agent_auth import AgentRateLimiter

limiter = AgentRateLimiter()
try:
    if limiter.check_rate_limit('agent_id'):
        # Allow request
        pass
except RateLimitExceeded:
    # Reject request (429)
    pass
```

### Log Submission
```python
from apps.certificates.agent_auth import AgentAuditLogger

logger = AgentAuditLogger()
logger.log_submission(
    agent_id='...',
    hostname='SERVER01',
    cert_count=5,
    status='success',
    error=None
)
```

---

## 📊 Database Schemas

### Certificate Model (Extended)
```python
class Certificate(models.Model):
    # ... existing fields ...
    hostname = CharField(max_length=255, null=True, blank=True)
    template_name = CharField(max_length=255, null=True, blank=True)
    agent_id = CharField(max_length=100, null=True, blank=True)
```

### AgentToken Model
```python
class AgentToken(models.Model):
    token = CharField(max_length=40, unique=True)
    agent_name = CharField(max_length=255)
    hostname = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    last_used = DateTimeField(null=True, blank=True)
    active = BooleanField(default=True)
```

### AgentAuditLog Model
```python
class AgentAuditLog(models.Model):
    agent_id = CharField(max_length=100)
    hostname = CharField(max_length=255)
    timestamp = DateTimeField(auto_now_add=True)
    action = CharField(max_length=50)
    certificate_count = IntegerField(null=True)
    status = CharField(max_length=50)
    error = TextField(null=True, blank=True)
```

---

## 🧪 Testing Quick Ref

```bash
# Run all tests
python test_internal_certs.py "token_here"

# Expected output: 8/8 tests passed ✓

# Test cases:
# 1. Missing token (401) ✓
# 2. Valid single certificate (201) ✓
# 3. Duplicate thumbprint - upsert (200) ✓
# 4. Malformed JSON (400) ✓
# 5. Missing required field (400) ✓
# 6. Invalid token (401) ✓
# 7. Batch ingestion (200/201) ✓
# 8. Expired certificate - CRITICAL (100 risk) ✓
```

---

## ⚡ Common Commands

### List All Tokens
```bash
python manage.py shell
from apps.certificates.agent_auth import AgentToken
AgentToken.objects.all().values('agent_name', 'hostname', 'created_at', 'last_used')
```

### Revoke Token
```bash
python manage.py shell
from apps.certificates.agent_auth import AgentToken
t = AgentToken.objects.get(token='abc...')
t.active = False
t.save()
```

### View Recent Submissions
```bash
python manage.py shell
from apps.certificates.agent_auth import AgentAuditLog
AgentAuditLog.objects.all().order_by('-timestamp')[:10]
```

### Count Certificates by Hostname
```bash
python manage.py shell
from apps.certificates.models import Certificate
Certificate.objects.filter(source_type='internal_agent').values('hostname').annotate(count=models.Count('id'))
```

---

## 🎯 Risk Scoring

| Condition | Score | Level |
|-----------|-------|-------|
| Expired | 100 | 🔴 CRITICAL |
| ≤7 days | 90 | 🔴 CRITICAL |
| ≤30 days | 75 | 🟠 HIGH |
| ≤90 days | 50 | 🟡 MEDIUM |
| Valid + Secure | 0-25 | 🟢 LOW |
| + Key < 2048 | +20 | ↑ Increase |
| + Self-signed | +15 | ↑ Increase |

---

## 🛡️ Security Notes

- **Token Length:** 40 hex characters (cryptographically secure)
- **Rate Limit:** 100 requests/minute per agent
- **Duplicate Detection:** By thumbprint (prevents duplicates)
- **Audit Trail:** All submissions logged with timestamp, status, error
- **Authentication:** Agent token (separate from user JWT)
- **Data Validation:** Thumbprint, dates, required fields validated

---

## 🔗 PowerShell Integration

```powershell
# In AutoCollect-CertEye.ps1:

# Set these at the top:
$API_URL = "http://localhost:8000"
$AGENT_TOKEN = "abc123def456ghi789jkl0123456789mno456"
$ENDPOINT = "$API_URL/api/certificates/collect/"

# Collect certificates:
$certs = Get-ChildItem -Path Cert:\LocalMachine\My

# Build payload:
$payload = @{
    agent_token = $AGENT_TOKEN
    certificates = @(
        foreach ($cert in $certs) {
            @{
                hostname = $env:COMPUTERNAME
                subject = $cert.Subject
                issuer = $cert.Issuer
                thumbprint = $cert.Thumbprint
                valid_to = $cert.NotAfter
                template_name = $cert.Extensions | Where {$_.Oid.FriendlyName -eq "Certificate Template Name"} | Select Value
            }
        }
    )
}

# Send to API:
Invoke-RestMethod -Uri $ENDPOINT -Method Post -Body ($payload | ConvertTo-Json -Depth 10) -ContentType "application/json"
```

---

## 📝 File Structure

```
ssl_backend/apps/certificates/
├── models.py                 # Extended Certificate model
├── serializers.py            # Payload validation
├── views.py                  # API endpoints
├── internal_service.py       # Business logic (NEW)
├── agent_auth.py             # Authentication & audit (NEW)
└── test_internal_certs.py    # Test suite (NEW)

ssl_frontend/src/pages/
└── InternalCertificatesPage.jsx  # UI component (NEW)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| 401 Unauthorized | Check token exists: `AgentToken.objects.get(token='...')` |
| 429 Rate Limited | Wait 60 seconds, check if >100 req/min |
| Certificate not appearing | Verify API returned 200/201, source_type is 'internal_agent' |
| Tests fail | Run `python manage.py migrate` first |
| PowerShell fails | Check: token, API URL, network connectivity, cert store access |

---

## 📋 Deployment Checklist

- [ ] Run `makemigrations` + `migrate`
- [ ] Generate agent tokens for each machine
- [ ] Run test suite (8/8 pass)
- [ ] Test PowerShell submission
- [ ] Verify frontend displays certificates
- [ ] Test all filters work
- [ ] Check audit logs
- [ ] Set up monitoring/alerts
- [ ] Document for operations team

---

## 💡 Tips & Tricks

**Tip 1:** Batch multiple certificates in one request (more efficient)
```bash
{
  "agent_token": "...",
  "certificates": [cert1, cert2, cert3, ...]
}
```

**Tip 2:** CSV export from frontend for external reports
- Select certs → Click "Export" → Opens in Excel

**Tip 3:** Use hostname filter for per-server inventory
```bash
GET /api/certificates/?source_type=internal_agent&hostname=SERVER01
```

**Tip 4:** Monitor rate limiting to catch misconfigured agents
```bash
python manage.py shell
# Check AgentAuditLog for errors
```

**Tip 5:** Set up automatic renewal reminders
- Alert on certificates ≤30 days to expiry
- Frontend shows risk level "HIGH" 🟠

---

## 📚 Documentation Files

1. **`INTERNAL_CERTS_TESTING_GUIDE.md`** ← Start here (testing)
2. **`API_DOCUMENTATION_INTERNAL_CERTS.md`** ← Full API reference
3. **`INTERNAL_CERT_IMPLEMENTATION_COMPLETE.md`** ← Implementation details
4. **`QUICK_REFERENCE_CARD.md`** ← This file

---

## 🎯 What to Test First

1. ✓ Database migrations
2. ✓ Token generation
3. ✓ Single certificate submission
4. ✓ Batch submission
5. ✓ Duplicate handling
6. ✓ Frontend display
7. ✓ Filters
8. ✓ CSV export

---

**Last Updated:** January 2024
**Version:** 1.0
**Status:** ✅ Ready for Production
