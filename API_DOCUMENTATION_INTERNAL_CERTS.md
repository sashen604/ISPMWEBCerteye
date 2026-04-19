# Internal Certificate Collection API - Complete Documentation

## 📡 API Overview

The Internal Certificate Collection API enables PowerShell agents running on Windows machines to submit SSL/TLS certificates for centralized tracking and risk assessment.

**Base URL:** `http://localhost:8000` (development) or your production domain

**Authentication:** Agent Token (not user JWT)

**Rate Limiting:** 100 requests per minute per agent

---

## 🔑 Authentication

### Agent Token System

Instead of user JWT tokens, internal certificate collection uses dedicated **Agent Tokens** for machine-to-machine authentication.

#### Generate Token

```python
from apps.certificates.agent_auth import AgentAuthenticator

auth = AgentAuthenticator()
token = auth.generate_token(
    agent_name='PowerShell-Agent-Production-01',
    hostname='PROD-SERVER-01'
)

print(f"Token: {token}")  # 40-character hex string
```

#### Token Structure

- **Length:** 40 characters (cryptographically secure random hex)
- **Scope:** One token per agent/machine
- **Lifetime:** Indefinite until revoked
- **Tracking:** Last used timestamp recorded automatically

---

## 📮 Endpoints

### 1. Collect Internal Certificates

**Endpoint:** `POST /api/certificates/collect/`

**Description:** Submit one or more certificates from a Windows machine to the backend.

#### Request Format

```json
{
  "agent_token": "abc123def456ghi789jkl0123456789mno456",
  "hostname": "PROD-SERVER-01",
  "subject": "prod-server-01.example.com",
  "issuer": "Example Internal CA",
  "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
  "valid_from": "2023-01-15T10:30:00Z",
  "valid_to": "2025-01-15T10:30:00Z",
  "certificate_template": "WebServer",
  "signature_algorithm": "sha256WithRSAEncryption",
  "key_length": 2048
}
```

#### Batch Format

Submit multiple certificates in a single request:

```json
{
  "agent_token": "abc123def456ghi789jkl0123456789mno456",
  "certificates": [
    {
      "hostname": "PROD-SERVER-01",
      "subject": "prod-server-01.example.com",
      "issuer": "Example Internal CA",
      "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
      "valid_from": "2023-01-15T10:30:00Z",
      "valid_to": "2025-01-15T10:30:00Z",
      "certificate_template": "WebServer"
    },
    {
      "hostname": "PROD-SERVER-02",
      "subject": "prod-server-02.example.com",
      "issuer": "Example Internal CA",
      "thumbprint": "4A3616582C166AF1E93FBD5BC47D57B5F6453F1F",
      "valid_from": "2023-02-20T14:45:00Z",
      "valid_to": "2025-02-20T14:45:00Z",
      "certificate_template": "IIS"
    }
  ]
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_token` | string | ✅ | 40-character hex token for authentication |
| `hostname` | string | ✅ | Windows machine hostname |
| `subject` | string | ✅ | Certificate subject (CN) |
| `issuer` | string | ✅ | Certificate issuer |
| `thumbprint` | string | ✅ | Certificate thumbprint (40 hex chars, no spaces/colons) |
| `valid_from` | ISO datetime | ❌ | When certificate becomes valid (ISO 8601 format) |
| `valid_to` | ISO datetime | ✅ | When certificate expires (ISO 8601 format) |
| `certificate_template` | string | ❌ | Windows certificate template name |
| `signature_algorithm` | string | ❌ | Algorithm used (e.g., sha256WithRSAEncryption) |
| `key_length` | integer | ❌ | Key size in bits (e.g., 2048, 4096) |
| `certificates` | array | ❌ | Array of certificate objects for batch submission |

#### Response (Success - 201 Created or 200 OK)

**Single Certificate:**
```json
{
  "success": true,
  "message": "Certificate ingested successfully",
  "status": "created",
  "certificate": {
    "id": 123,
    "subject": "prod-server-01.example.com",
    "issuer": "Example Internal CA",
    "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
    "hostname": "PROD-SERVER-01",
    "template_name": "WebServer",
    "valid_from": "2023-01-15T10:30:00Z",
    "valid_to": "2025-01-15T10:30:00Z",
    "days_remaining": 387,
    "risk_level": "LOW",
    "risk_score": 15,
    "source_type": "internal_agent",
    "agent_id": "abc123def456ghi789jkl0123456789mno456",
    "created_at": "2024-01-10T09:15:32Z",
    "updated_at": "2024-01-10T09:15:32Z"
  },
  "created": true
}
```

**Batch Submission:**
```json
{
  "success": true,
  "message": "Batch ingestion completed",
  "total": 3,
  "created": 2,
  "updated": 1,
  "failed": 0,
  "results": [
    {
      "success": true,
      "certificate": {...},
      "status": "created"
    },
    {
      "success": true,
      "certificate": {...},
      "status": "updated"
    },
    {
      "success": true,
      "certificate": {...},
      "status": "created"
    }
  ]
}
```

#### Response (Errors)

**400 Bad Request - Invalid Payload:**
```json
{
  "success": false,
  "message": "Invalid payload: thumbprint must be 40 hex characters",
  "error": "VALIDATION_ERROR"
}
```

**401 Unauthorized - Invalid Token:**
```json
{
  "success": false,
  "message": "Invalid or expired agent token",
  "error": "AUTH_ERROR"
}
```

**429 Too Many Requests - Rate Limited:**
```json
{
  "success": false,
  "message": "Rate limit exceeded: 100 requests per minute per agent",
  "error": "RATE_LIMIT_ERROR"
}
```

#### Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Certificate updated (duplicate thumbprint) |
| `201` | Created | New certificate created |
| `400` | Bad Request | Invalid payload, missing required fields |
| `401` | Unauthorized | Invalid/missing agent token |
| `422` | Unprocessable Entity | Validation error (malformed data) |
| `429` | Too Many Requests | Rate limit exceeded |

---

### 2. List Internal Certificates

**Endpoint:** `GET /api/certificates/?source_type=internal_agent`

**Description:** Retrieve internal certificates with optional filtering.

**Authentication:** Required (user JWT or authenticated session)

#### Query Parameters

```
GET /api/certificates/?source_type=internal_agent&hostname=PROD-SERVER-01&risk_level=CRITICAL
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_type` | string | Filter by source: `internal_agent` |
| `hostname` | string | Filter by Windows hostname |
| `template_name` | string | Filter by certificate template |
| `risk_level` | string | Filter by risk: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `status` | string | Filter by status: `valid`, `expiring_soon`, `expired` |
| `days_remaining` | integer | Filter certificates expiring within N days |
| `search` | string | Search subject, issuer, hostname |
| `ordering` | string | Sort by field: `hostname`, `valid_to`, `risk_score`, `-created_at` |
| `page` | integer | Pagination page number (default: 1) |
| `limit` | integer | Items per page (default: 20) |

#### Request Example

```bash
curl http://localhost:8000/api/certificates/?source_type=internal_agent&hostname=PROD-SERVER-01 \
  -H "Authorization: Bearer your_jwt_token"
```

#### Response

```json
{
  "count": 5,
  "next": "http://localhost:8000/api/certificates/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "subject": "prod-server-01.example.com",
      "issuer": "Example Internal CA",
      "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
      "hostname": "PROD-SERVER-01",
      "template_name": "WebServer",
      "valid_from": "2023-01-15T10:30:00Z",
      "valid_to": "2025-01-15T10:30:00Z",
      "days_remaining": 387,
      "risk_level": "LOW",
      "risk_score": 15,
      "source_type": "internal_agent",
      "created_at": "2024-01-10T09:15:32Z",
      "updated_at": "2024-01-10T09:15:32Z"
    },
    ...
  ]
}
```

---

### 3. Agent Status

**Endpoint:** `GET /api/certificates/agent_status/`

**Description:** Get submission statistics and status for all agents.

**Authentication:** Required (user JWT or authenticated session)

#### Request Example

```bash
curl http://localhost:8000/api/certificates/agent_status/ \
  -H "Authorization: Bearer your_jwt_token"
```

#### Response

```json
{
  "agents": [
    {
      "agent_id": "abc123def456ghi789jkl0123456789mno456",
      "agent_name": "PowerShell-Agent-01",
      "hostname": "PROD-SERVER-01",
      "status": "connected",
      "last_submission": "2024-01-10T14:23:15Z",
      "certificate_count": 5,
      "submissions_24h": 8,
      "success_rate": 0.95,
      "last_error": null
    },
    {
      "agent_id": "xyz789abc123def456ghi789jkl0123456789",
      "agent_name": "PowerShell-Agent-02",
      "hostname": "PROD-SERVER-02",
      "status": "offline",
      "last_submission": "2024-01-09T08:45:30Z",
      "certificate_count": 3,
      "submissions_24h": 0,
      "success_rate": 1.0,
      "last_error": null
    }
  ],
  "summary": {
    "total_agents": 2,
    "active_agents": 1,
    "offline_agents": 1,
    "total_certificates": 8,
    "submissions_24h": 8,
    "avg_success_rate": 0.975
  }
}
```

---

## 🏗️ Payload Validation Rules

### Thumbprint Validation
- **Format:** 40 hexadecimal characters (case-insensitive)
- **Accepted:** `3F2505471B1559F0D91EBC4AB39C46A4E5342F0E`
- **Rejected:** `3F:25:05:47:1B:15:59:F0:D9:1E:BC:4A:B3:9C:46:A4:E5:34:2F:0E` (with colons)
- **Rejected:** `3F250547` (too short)

### Date/Time Validation
- **Format:** ISO 8601 (UTC timezone)
- **Accepted:** 
  - `2025-01-15T10:30:00Z`
  - `2025-01-15T10:30:00+00:00`
  - `2025-01-15T10:30:00.000Z`
- **Rejected:**
  - `01/15/2025` (not ISO format)
  - `2025-01-15 10:30:00` (no Z or +00:00)

### Hostname Validation
- **Format:** Windows machine hostname
- **Accepted:**
  - `PROD-SERVER-01`
  - `prod-server-01`
  - `PROD_SERVER_01`
- **Length:** 1-255 characters
- **Note:** Case-insensitive in database queries

---

## 🎯 Risk Level Calculation

Risk scores are automatically calculated based on certificate properties:

### Scoring Algorithm

```
Base Score = 0 (default for valid, secure certificates)

Adjustments:
- Expired: +100 (CRITICAL 🔴)
- ≤7 days until expiry: +90 (CRITICAL 🔴)
- ≤30 days until expiry: +75 (HIGH 🟠)
- ≤90 days until expiry: +50 (MEDIUM 🟡)
- Key length < 2048 bits: +20
- Self-signed certificate: +15
- Algorithm weakness: +10

Final Score Range:
- 0-25: LOW 🟢
- 26-50: MEDIUM 🟡
- 51-80: HIGH 🟠
- 81-100: CRITICAL 🔴
```

### Examples

| Scenario | Score | Level |
|----------|-------|-------|
| Expires in 400 days, 2048-bit RSA | 0-25 | LOW |
| Expires in 60 days, 2048-bit RSA | 50 | MEDIUM |
| Expires in 10 days, 2048-bit RSA | 90 | CRITICAL |
| Expired 1 day ago | 100 | CRITICAL |
| 1024-bit RSA, expires in 90 days | 70 | HIGH |
| Self-signed, expires in 30 days | 90 | CRITICAL |

---

## ⏱️ Rate Limiting Details

**Limit:** 100 requests per minute per agent

**Behavior:**
- Requests are counted per agent token
- Counter resets every 60 seconds
- Excess requests return 429 Too Many Requests
- Last-Used timestamp is updated on each successful request

**Example:**
```
Request 1-100: ✅ 200 OK (accepted)
Request 101: ❌ 429 Too Many Requests (rate limited)
Wait 60 seconds...
Request 102: ✅ 200 OK (counter resets)
```

### Why 100 requests/minute?

- **PowerShell batch submissions:** ~3-10 certificates per request
- **Typical load per agent:** 1-5 submissions per hour
- **Burst capacity:** Supports up to 1000 certs/min per agent
- **Protection:** Prevents misconfigured agents from overwhelming backend

---

## 🔄 Duplicate Handling (Upsert)

When a certificate with the same **thumbprint** is submitted again:

### First Submission (Create)
```
POST /api/certificates/collect/
{
  "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
  "subject": "server.example.com",
  ...
}

Response: 201 Created
{
  "success": true,
  "status": "created",
  "certificate": {...}
}
```

### Second Submission (Update)
```
POST /api/certificates/collect/
{
  "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
  "subject": "server.example.com",  # Can be same or different
  "valid_to": "2025-02-15T...",     # Updated value
  ...
}

Response: 200 OK
{
  "success": true,
  "status": "updated",
  "certificate": {...}  # Same ID, updated fields
}
```

**Benefits:**
- Prevents duplicate certificates in database
- Updates expiration dates, risk scores automatically
- Tracks certificate history per thumbprint
- Efficient storage

---

## 🧪 Testing Examples

### Using curl

#### Single Certificate
```bash
curl -X POST http://localhost:8000/api/certificates/collect/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_token": "abc123def456ghi789jkl0123456789mno456",
    "hostname": "PROD-SERVER-01",
    "subject": "prod-server-01.example.com",
    "issuer": "Example Internal CA",
    "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
    "valid_to": "2025-12-31T23:59:59Z",
    "certificate_template": "WebServer",
    "key_length": 2048
  }'
```

#### Batch Submission
```bash
curl -X POST http://localhost:8000/api/certificates/collect/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_token": "abc123def456ghi789jkl0123456789mno456",
    "certificates": [
      {
        "hostname": "PROD-SERVER-01",
        "subject": "prod-server-01.example.com",
        "issuer": "Example Internal CA",
        "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
        "valid_to": "2025-12-31T23:59:59Z"
      },
      {
        "hostname": "PROD-SERVER-02",
        "subject": "prod-server-02.example.com",
        "issuer": "Example Internal CA",
        "thumbprint": "4A3616582C166AF1E93FBD5BC47D57B5F6453F1F",
        "valid_to": "2025-12-31T23:59:59Z"
      }
    ]
  }'
```

### Using Python

```python
import requests

token = "abc123def456ghi789jkl0123456789mno456"
url = "http://localhost:8000/api/certificates/collect/"

payload = {
    "agent_token": token,
    "hostname": "PROD-SERVER-01",
    "subject": "prod-server-01.example.com",
    "issuer": "Example Internal CA",
    "thumbprint": "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E",
    "valid_to": "2025-12-31T23:59:59Z",
}

response = requests.post(url, json=payload)
print(response.status_code)  # 201 Created
print(response.json())
```

### Using PowerShell

```powershell
$token = "abc123def456ghi789jkl0123456789mno456"
$url = "http://localhost:8000/api/certificates/collect/"

$cert = @{
    agent_token = $token
    hostname = "PROD-SERVER-01"
    subject = "prod-server-01.example.com"
    issuer = "Example Internal CA"
    thumbprint = "3F2505471B1559F0D91EBC4AB39C46A4E5342F0E"
    valid_to = "2025-12-31T23:59:59Z"
}

$response = Invoke-RestMethod -Uri $url -Method Post -Body ($cert | ConvertTo-Json) -ContentType "application/json"
$response | ConvertTo-Json
```

---

## 📋 Error Codes Reference

| Code | Status | Meaning | Solution |
|------|--------|---------|----------|
| `VALIDATION_ERROR` | 400 | Invalid payload format | Check required fields, data types |
| `AUTH_ERROR` | 401 | Invalid/missing token | Generate new token, verify token is active |
| `RATE_LIMIT_ERROR` | 429 | Too many requests | Wait 60 seconds, retry |
| `DB_ERROR` | 500 | Database error | Contact support, check server logs |
| `UNKNOWN_ERROR` | 500 | Unexpected error | Check server logs, retry later |

---

## 🔒 Security Best Practices

1. **Token Management**
   - Store tokens securely (not in plain text)
   - Rotate tokens periodically
   - One token per agent/machine
   - Never share tokens between machines

2. **API Requests**
   - Always use HTTPS in production
   - Include agent token in request body (not URL)
   - Validate response status codes
   - Handle errors gracefully

3. **Audit & Monitoring**
   - Monitor rate limit violations
   - Review audit logs regularly
   - Alert on failed authentication attempts
   - Track certificate changes

4. **PowerShell Script**
   - Restrict script execution permissions
   - Store token in secure location
   - Enable script logging
   - Test on non-production first

---

## 📞 Support & Troubleshooting

**Common Issues:**

**Q: I get 401 Unauthorized**
```
A: Check that:
   - Token is correct (no typos, right case)
   - Token is active in database
   - Token hasn't been revoked
```

**Q: I get 429 Rate Limited**
```
A: Reduce request frequency:
   - Batch multiple certificates into one request
   - Add delays between submissions
   - Contact admin to increase limit if needed
```

**Q: Certificate not appearing in frontend**
```
A: Verify:
   - API response shows 200/201 status
   - source_type is set to 'internal_agent'
   - Check browser network tab for API errors
   - Verify frontend has permission to view internal certs
```

**Q: How do I revoke an agent token?**
```
A: Use Django shell:
   from apps.certificates.agent_auth import AgentToken
   token = AgentToken.objects.get(token='your_token')
   token.active = False
   token.save()
```

---

**Last Updated:** January 2024
**Version:** 1.0
