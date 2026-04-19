# Internal Certificate Collection - Testing & Deployment Guide

## 📋 Prerequisites

- ✅ All code components created (internal_service.py, agent_auth.py, views.py updated)
- ✅ Frontend page created (InternalCertificatesPage.jsx)
- ✅ Test script ready (test_internal_certs.py)
- ✅ Backend and frontend servers can run

## 🚀 Phase 1: Database Setup (5 minutes)

### Step 1.1: Create Django Migrations

```bash
cd ssl_backend

# Create migrations for new Certificate fields and agent models
python manage.py makemigrations

# Expected output should show:
# - Migration for Certificate model (hostname, template_name, agent_id fields)
# - Migration for AgentToken model
# - Migration for AgentAuditLog model
```

### Step 1.2: Apply Migrations

```bash
# Apply all pending migrations
python manage.py migrate

# Expected: Should show "Ran X migrations" with green checkmarks
# This creates the required database tables for agent tokens and audit logs
```

### Step 1.3: Verify Database Tables

```bash
# Open Django shell to verify tables exist
python manage.py shell

# In the shell:
from django.db import connection
from django.db.backends.sqlite3.base import DatabaseIntrospection

cursor = connection.cursor()
inspector = DatabaseIntrospection(connection)

# List all tables
tables = inspector.table_names()
print("Tables created:")
for table in sorted(tables):
    if 'certificate' in table.lower() or 'agent' in table.lower():
        print(f"  - {table}")

# Exit shell
exit()
```

## 🔑 Phase 2: Generate Agent Tokens (2 minutes)

### Step 2.1: Generate First Agent Token

```bash
cd ssl_backend
python manage.py shell

# Import the authenticator
from apps.certificates.agent_auth import AgentAuthenticator

# Create authenticator instance
auth = AgentAuthenticator()

# Generate token for PowerShell agent
token = auth.generate_token(
    agent_name='PowerShell-Agent-01',
    hostname='SERVER01'
)

print(f"Agent Token: {token}")
print("Save this token - you'll need it in the PowerShell script!")

# Optional: Generate tokens for additional agents
token2 = auth.generate_token(
    agent_name='PowerShell-Agent-02',
    hostname='SERVER02'
)

exit()
```

**Expected Output:**
```
Agent Token: abc123def456ghi789jkl0123456789mno456
Save this token - you'll need it in the PowerShell script!
```

### Step 2.2: List All Active Tokens

```bash
python manage.py shell

from apps.certificates.agent_auth import AgentToken

# List all tokens
tokens = AgentToken.objects.filter(active=True)
for token in tokens:
    print(f"Agent: {token.agent_name}")
    print(f"  Hostname: {token.hostname}")
    print(f"  Token: {token.token}")
    print(f"  Created: {token.created_at}")
    print(f"  Last Used: {token.last_used}")
    print()

exit()
```

## 🧪 Phase 3: Test the API (15 minutes)

### Step 3.1: Install Test Dependencies

```bash
# Ensure requests library is installed
pip install requests

# Verify
python -c "import requests; print(requests.__version__)"
```

### Step 3.2: Run Automated Test Suite

```bash
cd ssl_backend

# Run tests with your agent token (replace with actual token)
python apps/certificates/test_internal_certs.py "your_agent_token_here"

# Example:
python apps/certificates/test_internal_certs.py "abc123def456ghi789jkl0123456789mno456"
```

**Expected Output:**
```
============================================================
Internal Certificate Collection API - Test Suite
============================================================

[Test 1] Missing agent token
  Status: 401 (expected 401) ✓
  Message: Missing or invalid agent token

[Test 2] Valid single certificate
  Status: 201 ✓
  Message: Certificate ingested successfully
  Certificate ID: 42

[Test 3] Duplicate thumbprint (upsert)
  Status: 200 ✓
  Status: updated (expected 'updated') ✓
  Message: Certificate updated

[Test 4] Malformed JSON
  Status: 400 (expected 400 or 422) ✓

[Test 5] Missing required field (thumbprint)
  Status: 400 (expected 400) ✓
  Message: Missing required field: thumbprint

[Test 6] Invalid agent token
  Status: 401 (expected 401) ✓
  Message: Invalid agent token

[Test 7] Batch ingestion
  HTTP Status: 200 ✓
  Total: 3 | Created: 3 | Updated: 0 | Failed: 0

[Test 8] Expired certificate (should mark as CRITICAL)
  Risk Level: CRITICAL (expected CRITICAL) ✓
  Risk Score: 100 (expected 100) ✓

============================================================
Test Results Summary
============================================================
Test 1: Missing token                              ✓ PASS
Test 2: Valid single certificate                  ✓ PASS
Test 3: Duplicate thumbprint                      ✓ PASS
Test 4: Malformed JSON                            ✓ PASS
Test 5: Missing required field (thumbprint)       ✓ PASS
Test 6: Invalid agent token                       ✓ PASS
Test 7: Batch ingestion                           ✓ PASS
Test 8: Expired certificate (should mark CRITICAL) ✓ PASS

Total                                             8/8 passed

🎉 All tests passed!
```

### Step 3.3: Manual API Test with curl

```bash
# Test 1: Valid certificate submission
curl -X POST http://localhost:8000/api/certificates/collect/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_token": "your_agent_token_here",
    "hostname": "TEST-SERVER",
    "subject": "test.example.com",
    "issuer": "Example CA",
    "thumbprint": "ABCD1234567890ABCD1234567890ABCD12345678",
    "valid_to": "2025-12-31T23:59:59Z",
    "certificate_template": "WebServer"
  }'

# Expected: 201 Created with certificate data

# Test 2: List internal certificates
curl http://localhost:8000/api/certificates/?source_type=internal_agent \
  -H "Authorization: Bearer your_jwt_token"

# Expected: List of internal certificates

# Test 3: Filter by hostname
curl http://localhost:8000/api/certificates/?source_type=internal_agent&hostname=TEST-SERVER \
  -H "Authorization: Bearer your_jwt_token"

# Expected: Filtered list of certificates
```

### Step 3.4: Test Rate Limiting

```python
# Create a script to test rate limiting (max 100 requests/minute per agent)

import requests
import time
from concurrent.futures import ThreadPoolExecutor

token = "your_agent_token_here"
base_url = "http://localhost:8000"

def send_request(i):
    payload = {
        'agent_token': token,
        'hostname': f'RATELIMIT-TEST-{i}',
        'subject': f'ratelimit{i}.example.com',
        'issuer': 'Example CA',
        'thumbprint': f'{i:040X}',  # Unique thumbprint
        'valid_to': '2025-12-31T23:59:59Z',
    }
    
    response = requests.post(
        f"{base_url}/api/certificates/collect/",
        json=payload,
        timeout=5
    )
    
    return response.status_code, response.json().get('message', 'No message')

# Send 150 requests rapidly (should hit rate limit after ~100)
print("Testing rate limiting (sending 150 requests)...")

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(send_request, range(150)))

# Count responses
successes = sum(1 for status, _ in results if status in (200, 201))
rate_limited = sum(1 for status, _ in results if status == 429)

print(f"Successful: {successes}")
print(f"Rate limited (429): {rate_limited}")
print(f"Expected: ~100 successful, ~50 rate limited")
```

## 🎯 Phase 4: PowerShell Agent Integration (5 minutes)

### Step 4.1: Configure PowerShell Script

Edit the PowerShell script at `powershell/AutoCollect-CertEye.ps1`:

```powershell
# At the top of the script, set your environment variables:
$API_URL = "http://localhost:8000"
$API_ENDPOINT = "$API_URL/api/certificates/collect/"
$AGENT_TOKEN = "your_agent_token_here"  # From Step 2

# The script should already have logic to:
# 1. Collect certificates from Cert:\LocalMachine\My
# 2. Extract: subject, issuer, thumbprint, valid_from, valid_to
# 3. Format as JSON
# 4. Send to the API endpoint

# Test the script on a Windows machine:
powershell -ExecutionPolicy Bypass -File "C:\path\to\AutoCollect-CertEye.ps1"
```

### Step 4.2: Verify PowerShell Submission

After running the PowerShell script:

```bash
# Check backend logs
cd ssl_backend
tail -f /path/to/logs/django.log  # If logging to file

# Or use Django shell to check audit logs
python manage.py shell

from apps.certificates.agent_auth import AgentAuditLog

# View recent submissions
logs = AgentAuditLog.objects.all().order_by('-timestamp')[:10]
for log in logs:
    print(f"{log.timestamp} | {log.agent_id} | {log.hostname} | {log.certificate_count} certs | Status: {log.status}")

exit()
```

### Step 4.3: Verify Certificates in Frontend

```bash
# Start frontend (if not already running)
cd ssl_frontend
npm run dev

# Open browser to http://localhost:5173
# Navigate to "Internal Certificates" page
# Verify certificates appear in the table
# Test filters: hostname, template, risk level
```

## ✅ Phase 5: Comprehensive Testing Checklist

- [ ] **Database Setup**
  - [ ] Migrations created successfully
  - [ ] Migrations applied without errors
  - [ ] Agent tables exist in database

- [ ] **Token Generation**
  - [ ] Agent token generated successfully
  - [ ] Token is unique and cryptographically secure
  - [ ] Multiple tokens can be generated

- [ ] **API Tests**
  - [ ] Valid certificate accepted (201/200)
  - [ ] Duplicate thumbprint updates existing cert
  - [ ] Missing token returns 401
  - [ ] Invalid token returns 401
  - [ ] Malformed JSON returns 400
  - [ ] Missing required field returns 400
  - [ ] Rate limiting enforces 100 req/min
  - [ ] Batch ingestion works (3+ certs)
  - [ ] Expired certificates marked CRITICAL
  - [ ] Audit logs record all submissions

- [ ] **PowerShell Integration**
  - [ ] PowerShell script runs without errors
  - [ ] Certificates are collected from Windows store
  - [ ] JSON payload is well-formed
  - [ ] API accepts PowerShell submission
  - [ ] Certificates appear in database

- [ ] **Frontend Display**
  - [ ] Internal Certificates page loads
  - [ ] Certificates display in table
  - [ ] Hostname filter works
  - [ ] Template filter works
  - [ ] Risk level filter works
  - [ ] Expiration status filter works
  - [ ] CSV export works
  - [ ] Agent status panel shows connected agents
  - [ ] Expandable rows show full certificate details

- [ ] **Security**
  - [ ] Authentication prevents unauthorized access
  - [ ] Rate limiting blocks abuse attempts
  - [ ] Audit logs capture all submissions
  - [ ] Token can be revoked/disabled
  - [ ] Sensitive data not logged in plaintext

## 🐛 Troubleshooting

### Issue: Migration Fails
```bash
# Clear migrations and start fresh
python manage.py migrate certificates zero
python manage.py makemigrations certificates
python manage.py migrate certificates
```

### Issue: Agent Token Not Working
```bash
# Verify token in database
python manage.py shell
from apps.certificates.agent_auth import AgentToken
token = AgentToken.objects.get(token='your_token')
print(f"Active: {token.active}")
print(f"Last used: {token.last_used}")
# Reactivate if needed
token.active = True
token.save()
exit()
```

### Issue: Rate Limit Too Aggressive
Edit `ssl_backend/apps/certificates/agent_auth.py` and change:
```python
MAX_REQUESTS_PER_MINUTE = 100  # Change this value (default: 100)
```

### Issue: PowerShell Script Fails
```powershell
# Debug PowerShell script
$DebugPreference = "Continue"
# Run script with debug output
# Check for:
# - Certificate store access permissions
# - JSON serialization errors
# - Network connectivity to API
# - Token validity
```

## 📊 Monitoring & Maintenance

### View Agent Statistics
```bash
python manage.py shell

from apps.certificates.agent_auth import AgentAuditLog
from django.db.models import Count, Q
from datetime import datetime, timedelta

# Statistics for last 24 hours
cutoff = datetime.now() - timedelta(days=1)
logs = AgentAuditLog.objects.filter(timestamp__gte=cutoff)

print(f"Total submissions (24h): {logs.count()}")
print(f"Successful submissions: {logs.filter(status='success').count()}")
print(f"Failed submissions: {logs.filter(status='error').count()}")

# Per-agent statistics
for agent_id in logs.values('agent_id').distinct():
    agent_logs = logs.filter(agent_id=agent_id['agent_id'])
    total_certs = sum(log.certificate_count for log in agent_logs if log.certificate_count)
    print(f"\nAgent {agent_id['agent_id']}: {agent_logs.count()} submissions, {total_certs} certificates")

exit()
```

### Review Audit Logs
```bash
python manage.py shell

from apps.certificates.agent_auth import AgentAuditLog

# Show last 50 submissions
logs = AgentAuditLog.objects.all().order_by('-timestamp')[:50]
for log in logs:
    error_msg = f" | Error: {log.error}" if log.error else ""
    print(f"{log.timestamp} | {log.agent_id:20} | {log.hostname:20} | {log.certificate_count:3} | {log.status}{error_msg}")

exit()
```

## 🚀 Production Deployment

### Pre-deployment Checklist
- [ ] All tests pass
- [ ] PowerShell agents working on Windows machines
- [ ] Frontend displaying certificates correctly
- [ ] Audit logs working
- [ ] Rate limiting configured appropriately
- [ ] Agent tokens securely stored/distributed
- [ ] Database backups configured
- [ ] Error logging configured
- [ ] Monitoring/alerting set up

### Deployment Steps
1. Run migrations on production database
2. Generate agent tokens for all Windows machines
3. Distribute tokens to PowerShell agents
4. Monitor first batch of submissions
5. Verify frontend shows certificates
6. Enable automated collection (configure Windows Task Scheduler on agents)

## 📝 Summary

**Implementation Complete:**
- ✅ Database models created (Certificate extensions, AgentToken, AgentAuditLog)
- ✅ Backend service implemented (internal_service.py)
- ✅ Authentication system built (agent_auth.py with rate limiting)
- ✅ API endpoints created (3 new endpoints)
- ✅ Frontend page built (InternalCertificatesPage.jsx)
- ✅ Test suite created (test_internal_certs.py)

**Next Actions:**
1. Run Phase 1 (Database setup)
2. Run Phase 2 (Generate tokens)
3. Run Phase 3 (Automated tests)
4. Run Phase 4 (PowerShell integration)
5. Run Phase 5 (Manual verification checklist)
6. Deploy to production

**Estimated Time:** 30-45 minutes total
