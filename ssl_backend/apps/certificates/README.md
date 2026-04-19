# SSL/TLS Certificate Scanning Service

Complete guide for the SSL/TLS certificate retrieval, parsing, and storage system implemented in Django.

## Overview

The certificate scanning service is a production-grade system for:
- **Fetching** SSL/TLS certificates from HTTPS domains
- **Parsing** X.509 certificate metadata
- **Storing** certificate data in PostgreSQL
- **Risk Scoring** based on expiration and key length
- **Managing** certificates via REST API or CLI

## Architecture

### Component Structure

```
ssl_backend/apps/certificates/
├── models.py              # Certificate ORM model (14 fields)
├── serializers.py         # DRF serializers for API responses
├── views.py               # REST API viewset with scan endpoints
├── urls.py                # URL routing with DRF router
├── admin.py               # Django admin interface
│
├── fetchers.py            # Low-level certificate retrieval
│   └── SSLCertificateFetcher class
│       - fetch_certificate()      - Connect to domain:port and retrieve cert
│       - fetch_from_any_port()    - Try multiple ports (443, 8443)
│
├── parsers.py             # Certificate metadata extraction
│   └── CertificateParser class
│       - parse_certificate()      - Extract all certificate fields
│       - _extract_subject_name()  - Parse subject DN
│       - _extract_issuer_name()   - Parse issuer DN
│       - _parse_asn1_date()       - Convert ASN.1 dates to Python datetime
│       - _determine_certificate_type()  - Classify cert (wildcard, self-signed, etc)
│
├── services.py            # High-level orchestration
│   └── CertificateFetchService class
│       - scan_and_store()         - Complete workflow for single domain
│       - scan_multiple()          - Scan multiple domains with aggregation
│       - _calculate_risk()        - Generate risk scores and levels
│       - _store_or_update_certificate()  - Database operations
│
└── management/commands/
    └── scan_certificates.py       # Django CLI command for testing
```

### Data Flow

```
Domain Input
    ↓
[SSLCertificateFetcher]  ← Connects to HTTPS port 443/8443
    ↓ (X509 certificate object)
[CertificateParser]      ← Extracts metadata (issuer, subject, dates, etc.)
    ↓ (dict with parsed data)
[CertificateFetchService] ← Coordinates flow, calculates risk, handles database
    ↓ (transaction safe)
[Django ORM]             ← Stores in PostgreSQL
    ↓
[Certificate Model]      ← 14-field schema with indexes
```

## Database Schema

The `Certificate` model includes:

| Field | Type | Purpose |
|-------|------|---------|
| `domain` | CharField (indexed) | Domain name (e.g., google.com) |
| `certificate_type` | CharField | Classification (wildcard, single, multi-domain, self-signed, other) |
| `issuer` | CharField | Issuer distinguished name |
| `subject` | CharField | Subject distinguished name |
| `serial_number` | CharField (indexed, unique lookup) | Certificate serial number |
| `signature_algorithm` | CharField | Algorithm used (sha256WithRSAEncryption, etc.) |
| `key_length` | PositiveIntegerField | Key size in bits (2048, 4096, etc.) |
| `valid_from` | DateTimeField | Validity start (UTC) |
| `valid_to` | DateTimeField (indexed) | Expiration date (UTC) |
| `days_remaining` | IntegerField | Calculated days until expiration |
| `risk_level` | CharField | Assessment (low, medium, high, critical) |
| `risk_score` | PositiveIntegerField | Score 0-100 |
| `last_scanned` | DateTimeField | Timestamp of most recent scan |
| `source_type` | CharField | Source (agent, scanner, manual, etc.) |
| `status` | CharField | Status (active, expired, revoked) |
| `created_at` | DateTimeField (auto) | Record creation timestamp |
| `updated_at` | DateTimeField (auto) | Last record update timestamp |

## Usage

### 1. Command Line (Django Management Command)

#### Scan a Single Domain

```bash
cd ssl_backend
python manage.py scan_certificates google.com
```

**Output Example:**
```
📡 Starting certificate scan at 2026-04-17T14:30:00+00:00

✨ Created: google.com
   ├─ Subject:     CN=google.com, O=Google LLC, C=US
   ├─ Issuer:      CN=Google Internet Authority G3
   ├─ Serial:      1234567890abcdef
   ├─ Key Length:  2048 bits
   ├─ Algorithm:   sha256WithRSAEncryption
   ├─ Valid From:  2026-01-15T00:00:00+00:00
   ├─ Valid To:    2027-01-15T00:00:00+00:00
   ├─ Days Left:   283
   ├─ Risk Level:  low (5/100)
   └─ Type:        single

✅ Scan completed at 2026-04-17T14:30:02+00:00
```

#### Scan Multiple Domains

```bash
python manage.py scan_certificates google.com github.com amazon.com
```

#### Advanced Options

```bash
# Scan with 15-second timeout
python manage.py scan_certificates google.com --timeout 15

# Scan without updating existing certificates
python manage.py scan_certificates google.com --no-update

# Verbose output with certificate details
python manage.py scan_certificates google.com --verbose
```

### 2. REST API Endpoints

#### Single Domain Scan

**POST** `/api/certificates/scan/`

**Request:**
```json
{
    "domain": "example.com",
    "timeout": 10,
    "update_if_exists": true
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Certificate for example.com created successfully",
    "status": "created",
    "certificate": {
        "id": 1,
        "domain": "example.com",
        "certificate_type": "single",
        "issuer": "CN=Let's Encrypt Authority X3, O=Let's Encrypt, C=US",
        "subject": "CN=example.com, O=Example Inc, C=US",
        "serial_number": "abc123def456",
        "signature_algorithm": "sha256WithRSAEncryption",
        "key_length": 2048,
        "valid_from": "2026-04-17T00:00:00Z",
        "valid_to": "2027-04-17T00:00:00Z",
        "days_remaining": 365,
        "risk_level": "low",
        "risk_score": 5,
        "source_type": "scanner",
        "status": "active",
        "last_scanned": "2026-04-17T14:30:00Z",
        "created_at": "2026-04-17T14:30:00Z",
        "updated_at": "2026-04-17T14:30:00Z"
    },
    "error": null
}
```

**Response (Error):**
```json
{
    "success": false,
    "message": "Failed to fetch certificate from example.com",
    "status": "error",
    "certificate": null,
    "error": "Connection to example.com:443 timed out after 10s"
}
```

#### Batch Domain Scan

**POST** `/api/certificates/scan_batch/`

**Request:**
```json
{
    "domains": ["google.com", "github.com", "amazon.com"],
    "timeout": 10,
    "update_if_exists": true
}
```

**Response:**
```json
{
    "total": 3,
    "succeeded": 2,
    "failed": 1,
    "created": 2,
    "updated": 0,
    "results": [
        {
            "success": true,
            "message": "Certificate for google.com created successfully",
            "status": "created",
            "certificate": { ... },
            "error": null
        },
        {
            "success": true,
            "message": "Certificate for github.com updated successfully",
            "status": "updated",
            "certificate": { ... },
            "error": null
        },
        {
            "success": false,
            "message": "Failed to fetch certificate from amazon.com",
            "status": "error",
            "certificate": null,
            "error": "DNS resolution error: unknown host"
        }
    ]
}
```

#### List Certificates with Filters

**GET** `/api/certificates/`

**Query Parameters:**
```
?domain=google.com          # Search by domain
?risk_level=high            # Filter by risk level (low, medium, high, critical)
?certificate_type=wildcard  # Filter by type
?expiration_status=expiring_soon&expiring_days=30  # Expiring within 30 days
```

**Example:**
```bash
curl "http://localhost:8000/api/certificates/?domain=google.com&risk_level=low"
```

### 3. Python Service Usage (Programmatic)

```python
from apps.certificates.services import CertificateFetchService

# Initialize service with 10-second timeout
service = CertificateFetchService(timeout=10)

# Scan single domain
result = service.scan_and_store('google.com', update_if_exists=True)

if result['success']:
    cert = result['certificate']
    print(f"✅ {cert.domain} expires in {cert.days_remaining} days")
    print(f"   Risk: {cert.risk_level} ({cert.risk_score}/100)")
else:
    print(f"❌ Error: {result['error']}")

# Scan multiple domains
batch_result = service.scan_multiple(
    ['google.com', 'github.com', 'amazon.com'],
    update_if_exists=True
)

print(f"Succeeded: {batch_result['succeeded']}/{batch_result['total']}")
print(f"Created: {batch_result['created']}, Updated: {batch_result['updated']}")
```

## Risk Scoring Algorithm

Risk is calculated on a 0-100 scale based on:

### Expiration Risk
- Expires in < 7 days: +50
- Expires in < 30 days: +25
- Expires in < 90 days: +10

### Key Length Risk
- Key < 2048 bits: +30 (weak)
- Key < 4096 bits: +10 (acceptable)
- Key ≥ 4096 bits: 0 (strong)

### Certificate Type Risk
- Self-signed: +20
- Other types: 0

### Risk Level Classification
- Score > 70: **Critical** (red) - Immediate action required
- Score 50-70: **High** (orange) - Action required soon
- Score 25-50: **Medium** (yellow) - Monitor closely
- Score < 25: **Low** (green) - No immediate action

## Error Handling

### Exceptions

The service provides specific exceptions for different error scenarios:

```python
from apps.certificates.fetchers import (
    CertificateFetchError,      # Base exception
    ConnectionTimeoutError,      # Connection timeout
    InvalidCertificateError,     # Certificate parsing failed
    DNSResolutionError,          # Domain doesn't resolve
)

from apps.certificates.parsers import CertificateParsingError

try:
    result = service.scan_and_store('example.com')
except DNSResolutionError as e:
    print(f"Domain not found: {e}")
except ConnectionTimeoutError as e:
    print(f"Connection timeout: {e}")
except CertificateParsingError as e:
    print(f"Cannot parse certificate: {e}")
except CertificateFetchError as e:
    print(f"SSL/TLS error: {e}")
```

### Timeout Handling

```python
# 5-second timeout (aggressive)
service = CertificateFetchService(timeout=5)

# 30-second timeout (generous for slow servers)
service = CertificateFetchService(timeout=30)
```

## Django Admin Interface

Access at: `http://localhost:8000/admin/`

### Features

- **Color-coded displays**: Expiration status, risk level, key strength
- **Advanced filtering**: By status, risk level, certificate type, signature algorithm
- **Search**: By domain, subject, issuer, serial number
- **Bulk actions**: Mark as active/expired
- **Read-only access** for non-superusers
- **Expandable fieldsets**: Collapse detailed information
- **Audit trail**: View creation and update timestamps

### Admin Actions

```
✨ Created  - New certificate just scanned
🔄 Updated - Certificate details refreshed
❌ Expired - Certificate past expiration date
⚠️  Warning - Expires soon or weak key
✅ Valid   - Certificate is healthy
```

## Database Indexes

For performance optimization:

- `domain` - Indexed for quick domain searches
- `serial_number` - Indexed for duplicate detection
- `valid_to` - Indexed for expiration queries
- Combined indexes on common filter combinations

## Best Practices

### 1. Timeout Configuration
```python
# Default 10 seconds is good for most domains
# Increase for slow corporate environments
# Decrease for aggressive monitoring

service = CertificateFetchService(timeout=15)
```

### 2. Batch Processing
```python
# Process multiple domains in one call for better performance
domains = ['google.com', 'github.com', 'amazon.com']
result = service.scan_multiple(domains)
```

### 3. Duplicate Handling
```python
# Certificates are deduplicated by serial number
# If update_if_exists=True, existing certificates are refreshed
# If update_if_exists=False, existing certificates are skipped

result = service.scan_and_store('example.com', update_if_exists=True)
```

### 4. Error Recovery
```python
# The service catches all exceptions and returns them in the result
result = service.scan_and_store('invalid-domain-xyz-123.com')

if not result['success']:
    # Log error for retry or manual investigation
    error_message = result['error']
    log_certificate_scan_failure(error_message)
```

### 5. API Integration
```python
# From React frontend, use POST request with timeout
const scanCertificate = async (domain) => {
    const response = await fetch('/api/certificates/scan/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            domain: domain,
            timeout: 10,
            update_if_exists: true
        })
    });
    return response.json();
};
```

## Testing

### Unit Tests (Create `test_services.py`)

```python
from django.test import TestCase
from apps.certificates.services import CertificateFetchService
from apps.certificates.models import Certificate

class CertificateScanTests(TestCase):
    def setUp(self):
        self.service = CertificateFetchService(timeout=10)
    
    def test_scan_valid_domain(self):
        result = self.service.scan_and_store('google.com')
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'created')
    
    def test_invalid_domain(self):
        result = self.service.scan_and_store('invalid-xyz-domain-12345.test')
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_duplicate_detection(self):
        # First scan
        result1 = self.service.scan_and_store('google.com')
        self.assertEqual(result1['status'], 'created')
        
        # Second scan
        result2 = self.service.scan_and_store('google.com', update_if_exists=True)
        self.assertEqual(result2['status'], 'updated')
```

## Dependencies

Required packages (in `requirements.txt`):

```
Django>=5.0,<6.0
DjangoRESTFramework>=3.15,<4.0
django-cors-headers>=4.3,<5.0
psycopg2-binary>=2.9,<3.0
django-rest-framework-simplejwt>=5.3,<6.0
cryptography>=41.0.0
pyOpenSSL>=23.0.0
certifi>=2023.0.0
requests>=2.31.0
```

## Future Enhancements

- [ ] Scheduled certificate scanning with Celery
- [ ] Certificate transparency log validation
- [ ] Automated alerts for expiring certificates
- [ ] Certificate chain validation
- [ ] Support for client certificates (mTLS)
- [ ] Email notifications for risk changes
- [ ] Webhook integration for external systems
- [ ] Historical tracking of certificate changes
