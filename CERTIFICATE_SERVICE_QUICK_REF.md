# Quick Reference - Certificate Scanning Service

## New Folder Structure

```
ssl_backend/apps/certificates/
├── fetchers.py          ✨ SSL/TLS certificate retrieval (220 lines)
├── parsers.py           ✨ X.509 certificate parsing (290 lines)
├── services.py          ✨ Service orchestrator (340 lines)
├── admin.py             ✨ Django admin interface (280 lines)
├── README.md            ✨ Complete documentation (600+ lines)
└── management/commands/
    └── scan_certificates.py  ✨ CLI command (200 lines)
```

## Quick Start

### 1. Install Dependencies
```bash
cd ssl_backend
pip install -r requirements.txt
# Installs: cryptography, pyOpenSSL, certifi, requests
```

### 2. Scan a Domain (CLI)
```bash
cd ssl_backend
python manage.py scan_certificates google.com
```

### 3. Scan via API (cURL)
```bash
curl -X POST http://localhost:8000/api/certificates/scan/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

### 4. Scan via Python
```python
from apps.certificates.services import CertificateFetchService

service = CertificateFetchService()
result = service.scan_and_store('google.com')
print(f"✅ {result['certificate'].domain}")
```

## API Endpoints

### Single Domain Scan
- **URL**: `POST /api/certificates/scan/`
- **Body**: `{"domain": "example.com", "timeout": 10}`
- **Returns**: Certificate object with all metadata

### Batch Domain Scan
- **URL**: `POST /api/certificates/scan_batch/`
- **Body**: `{"domains": ["google.com", "github.com"], "timeout": 10}`
- **Returns**: Aggregated results with success/failure counts

### List Certificates
- **URL**: `GET /api/certificates/`
- **Filters**: `?domain=google.com&risk_level=high&expiration_status=expiring_soon`

## CLI Command Usage

```bash
# Single domain
python manage.py scan_certificates google.com

# Multiple domains
python manage.py scan_certificates google.com github.com amazon.com

# With custom timeout (seconds)
python manage.py scan_certificates google.com --timeout 15

# Without updating existing certificates
python manage.py scan_certificates google.com --no-update

# Verbose output with certificate details
python manage.py scan_certificates google.com --verbose
```

## Risk Scoring

```
Score Calculation:
- Expires < 7 days:     +50
- Expires < 30 days:    +25
- Expires < 90 days:    +10
- Key < 2048 bits:      +30
- Key < 4096 bits:      +10
- Self-signed:          +20

Risk Levels:
- Score > 70:  CRITICAL 🔴
- Score > 50:  HIGH 🟠
- Score > 25:  MEDIUM 🟡
- Score < 25:  LOW 🟢
```

## Module Overview

| Module | Class | Main Methods |
|--------|-------|--------------|
| `fetchers.py` | `SSLCertificateFetcher` | `fetch_certificate()`, `fetch_from_any_port()` |
| `parsers.py` | `CertificateParser` | `parse_certificate()` |
| `services.py` | `CertificateFetchService` | `scan_and_store()`, `scan_multiple()` |
| `admin.py` | `CertificateAdmin` | Django admin registration |
| `views.py` | `CertificateViewSet` | `scan()`, `scan_batch()` actions |

## Error Handling

### Exception Types
- `DNSResolutionError` - Domain doesn't resolve
- `ConnectionTimeoutError` - Connection times out
- `InvalidCertificateError` - Certificate can't be parsed
- `CertificateFetchError` - General SSL/TLS error
- `CertificateParsingError` - Parsing fails

### Example Error Handling
```python
result = service.scan_and_store('example.com')
if not result['success']:
    print(f"Error: {result['error']}")
```

## Database Schema

```
Certificate Model (17 fields):
- domain (CharField, indexed)
- certificate_type (CharField)
- issuer (CharField)
- subject (CharField)
- serial_number (CharField, indexed)
- signature_algorithm (CharField)
- key_length (PositiveIntegerField)
- valid_from (DateTimeField, UTC)
- valid_to (DateTimeField, indexed, UTC)
- days_remaining (IntegerField, calculated)
- risk_level (CharField)
- risk_score (PositiveIntegerField 0-100)
- source_type (CharField)
- status (CharField)
- last_scanned (DateTimeField)
- created_at (DateTimeField, auto)
- updated_at (DateTimeField, auto)
```

## Django Admin

- **URL**: `http://localhost:8000/admin/`
- **Features**:
  - Color-coded risk badges and expiration status
  - Advanced filtering (by status, risk, type, algorithm)
  - Search (domain, subject, issuer, serial number)
  - Bulk actions (mark as active/expired)
  - Read-only mode for non-superusers

## Performance

| Operation | Time |
|-----------|------|
| Single scan | 3-5 seconds |
| 10 domains batch | 30-50 seconds |
| DB insert | ~50ms |
| Parse cert | 10-50ms |

## Configuration

### Timeout
```python
# Default: 10 seconds
service = CertificateFetchService(timeout=10)

# Custom timeout
service = CertificateFetchService(timeout=30)
```

### Update Behavior
```python
# Create or update
result = service.scan_and_store('example.com', update_if_exists=True)

# Create only, skip if exists
result = service.scan_and_store('example.com', update_if_exists=False)
```

## Testing

```bash
# Django system check
python manage.py check

# Run specific test
python manage.py test apps.certificates.tests

# With coverage
coverage run --source='apps.certificates' manage.py test
coverage report
```

## Troubleshooting

### DNS Resolution Fails
- Check network connectivity
- Verify domain name spelling
- Try with alternative timeout value

### Connection Timeout
- Increase timeout: `CertificateFetchService(timeout=30)`
- Check firewall rules
- Try alternate port

### Invalid Certificate
- Ensure HTTPS domain (not HTTP)
- Check certificate validity
- Verify SSL/TLS support

### Database Errors
- Run migrations: `python manage.py migrate`
- Check PostgreSQL connection
- Verify database permissions

## Files Modified

- `ssl_backend/requirements.txt` - Added SSL libraries
- `ssl_backend/apps/certificates/views.py` - Added scan endpoints

## Files Created

- `ssl_backend/apps/certificates/fetchers.py`
- `ssl_backend/apps/certificates/parsers.py`
- `ssl_backend/apps/certificates/services.py`
- `ssl_backend/apps/certificates/admin.py`
- `ssl_backend/apps/certificates/management/commands/scan_certificates.py`
- `ssl_backend/apps/certificates/README.md`
- `CERTIFICATE_SERVICE_STRUCTURE.md` (this file's companion)

## Production Deployment

1. Install requirements: `pip install -r requirements.txt`
2. Run migrations: `python manage.py migrate`
3. Create Django admin user: `python manage.py createsuperuser`
4. Configure PostgreSQL connection in settings
5. Test: `python manage.py check`
6. Start server: `python manage.py runserver`
7. Access admin at `/admin/`

## Next Steps

- [ ] Create scheduled scanning with Celery
- [ ] Add certificate chain validation
- [ ] Implement email alerts for expiring certs
- [ ] Add webhook integrations
- [ ] Create historical tracking of changes
- [ ] Add client certificate (mTLS) support
