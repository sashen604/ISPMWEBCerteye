# AD CS Connector - Quick Reference Guide

## Quick Start

### For End Users

1. **Register AD CS Server**
   - Go to Admin Dashboard → AD CS Management
   - Click "Register New AD CS Source"
   - Fill in server details (hostname, IP, CA name, domain)
   - Enter service account credentials
   - Choose authentication method (WinRM recommended)
   - Click "Register"

2. **Test Connection**
   - Select registered source
   - Click "Test Connection"
   - View results (connected/error message)

3. **Sync Certificates**
   - Click "Sync Now" on source card
   - Wait for sync to complete
   - View imported count and any errors
   - Certificates appear in main dashboard

### For Developers

#### To Add AD CS to Your Install

1. **Run Migrations**
   ```bash
   cd ssl_backend
   python manage.py migrate
   ```

2. **Import Component**
   ```jsx
   import ADCSSourceForm from './components/ADCSSourceForm';
   ```

3. **Add to Navigation**
   ```jsx
   <Route path="/admin/adcs" element={<ADCSSourceForm />} />
   ```

4. **Include CSS**
   ```jsx
   import '../styles/adcs.css';
   ```

#### To Use AD CS API

```bash
# Register source
curl -X POST http://localhost:8000/api/certificates/adcs-sources/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Production-CA",
    "server_hostname": "ca.example.com",
    "server_ip": "192.168.1.100",
    "ca_name": "Example-CA",
    "domain": "example.com",
    "username": "admin",
    "password": "SecurePassword123",
    "auth_type": "winrm"
  }'

# Test connection
curl -X POST http://localhost:8000/api/certificates/adcs-sources/1/test_connection/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sync certificates
curl -X POST http://localhost:8000/api/certificates/adcs-sources/1/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get sync history
curl http://localhost:8000/api/certificates/adcs-sources/1/sync_history/?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Architecture Overview

```
AD CS Server (Windows)
    ↓ (WinRM/LDAP)
Connector Factory
    ├─ WinRMConnector (Primary)
    ├─ LDAPConnector (Secondary)
    └─ AgentConnector (Fallback)
    ↓
AD CS Integration Service
    ├─ test_connection()
    └─ sync_certificates()
    ↓
Certificate Processing
    ├─ Create/Update Certificates
    ├─ Create AD CS Metadata
    ├─ Calculate Risk Scores
    └─ Record Sync History
    ↓
CertEye Database
    ├─ ADCSSource (config)
    ├─ ADCSSyncHistory (tracking)
    ├─ ADCSCredentialHistory (audit)
    ├─ ADCSConnectionTest (results)
    ├─ ADCSCertificate (metadata)
    └─ Certificate (main records)
```

---

## File Locations

| Component | Path |
|-----------|------|
| Models | `ssl_backend/apps/certificates/models_adcs.py` |
| Encryption | `ssl_backend/apps/certificates/adcs_crypto.py` |
| Connectors | `ssl_backend/apps/certificates/adcs_connector.py` |
| Service | `ssl_backend/apps/certificates/adcs_service.py` |
| Serializers | `ssl_backend/apps/certificates/adcs_serializers.py` |
| Views | `ssl_backend/apps/certificates/adcs_views.py` |
| Frontend | `ssl_frontend/src/components/ADCSSourceForm.jsx` |
| Styles | `ssl_frontend/src/styles/adcs.css` |
| Migration | `ssl_backend/apps/certificates/migrations/0005_adcs_models.py` |

---

## Database Schema

### ADCSSource
```
- id: BigAutoField
- source_name: CharField (unique)
- description: TextField
- server_hostname: CharField (FQDN/IP)
- server_ip: CharField (IPv4/IPv6)
- ca_name: CharField
- domain: CharField
- username: CharField
- encrypted_password: TextField
- auth_type: CharField (winrm/ldap/agent)
- port: PositiveIntegerField
- use_ssl: BooleanField
- verify_ssl: BooleanField
- connection_status: CharField
- last_connection_at: DateTimeField
- auto_sync_enabled: BooleanField
- sync_interval_hours: PositiveIntegerField
- last_sync_at: DateTimeField
- certificate_count: PositiveIntegerField
- is_active: BooleanField
- created_by: ForeignKey(User)
- created_at: DateTimeField
- updated_at: DateTimeField

Indexes:
- (is_active, ca_name)
- (connection_status)
- (last_sync_at)
```

### ADCSSyncHistory
```
- id: BigAutoField
- source: ForeignKey(ADCSSource)
- sync_type: CharField (manual/scheduled/on_demand)
- status: CharField (pending/in_progress/success/partial_success/failed)
- certificates_fetched: PositiveIntegerField
- certificates_imported: PositiveIntegerField
- certificates_updated: PositiveIntegerField
- certificates_failed: PositiveIntegerField
- error_message: TextField
- sync_details: JSONField
- started_at: DateTimeField
- completed_at: DateTimeField
- duration_seconds: PositiveIntegerField
- triggered_by: ForeignKey(User)

Indexes:
- (source, started_at)
- (status)
```

### ADCSCertificate
```
- id: BigAutoField
- certificate: OneToOneField(Certificate)
- source: ForeignKey(ADCSSource)
- request_id: CharField (unique)
- template_name: CharField
- requester: CharField
- approver: CharField
- status_code: PositiveIntegerField
- dns_names: JSONField
- issued_at: DateTimeField
- renewed_at: DateTimeField
- revoked_at: DateTimeField
- imported_at: DateTimeField
- last_verified_at: DateTimeField

Indexes:
- (source, template_name)
- (request_id)
```

---

## Key Classes & Methods

### ADCSCredentialEncryption
```python
encrypt(plaintext: str) → str
decrypt(encrypted: str) → str
hash_password(password: str) → str
get_encryption_key() → bytes
```

### ADCSConnectorFactory
```python
create_connector(source: ADCSSource) → ADCSConnector
```

### ADCSIntegrationService
```python
test_connection(source, user=None, ip_address=None) → Dict
sync_certificates(source, user=None, ip_address=None) → Dict
_process_certificate(cert_data, source, stats) → None
_calculate_risk_score(cert, cert_data) → None
```

### ADCSSourceViewSet
```python
list()
create()
retrieve()
update()
destroy()
test_connection(request, pk=None)
sync(request, pk=None)
sync_history(request, pk=None)
connection_tests(request, pk=None)
```

---

## Common Tasks

### Adding a New AD CS Source Programmatically

```python
from apps.certificates.models_adcs import ADCSSource
from apps.certificates.adcs_crypto import ADCSCredentialEncryption

# Create source
source = ADCSSource.objects.create(
    source_name="New-CA",
    server_hostname="ca.example.com",
    server_ip="192.168.1.101",
    ca_name="NewCA",
    domain="example.com",
    username="admin",
    encrypted_password=ADCSCredentialEncryption.encrypt("password"),
    auth_type="winrm",
    port=5986,
    use_ssl=True
)
```

### Testing Connection

```python
from apps.certificates.adcs_service import ADCSIntegrationService

result = ADCSIntegrationService.test_connection(source)
print(result)  # {'success': True/False, 'message': '...', ...}
```

### Syncing Certificates

```python
result = ADCSIntegrationService.sync_certificates(source, user=request.user)
print(f"Imported: {result['stats']['certificates_imported']}")
```

### Querying Sync History

```python
from apps.certificates.models_adcs import ADCSSyncHistory

history = ADCSSyncHistory.objects.filter(source=source).order_by('-started_at')[:10]
for sync in history:
    print(f"{sync.status}: {sync.certificates_imported} imported in {sync.duration_seconds}s")
```

---

## Troubleshooting

### Issue: PowerShell Not Found (on Linux)

**Solution**: Mock mode automatically activates. For real testing, use Windows server or install WSL.

### Issue: Connection Test Fails

**Check**:
1. Server hostname/IP is correct
2. Port is open (5985=HTTP, 5986=HTTPS)
3. Username/password correct
4. Network connectivity to server
5. AD Certificate Services installed on server

**Debug**:
```python
from apps.certificates.adcs_connector import WinRMConnector
connector = WinRMConnector(source)
success, message = connector.test_connection()
print(f"Test result: {success}, Message: {message}")
```

### Issue: Certificate Import Fails

**Check**:
1. Sync connected successfully before importing
2. Certificates have unique thumbprints
3. Database constraints not violated
4. Disk space available

**Debug**:
```python
# Check sync history for error details
sync_history = ADCSSyncHistory.objects.get(id=sync_history_id)
print(sync_history.error_message)
print(sync_history.sync_details)
```

### Issue: API Returns 403 Forbidden

**Solution**: User must be superadmin or admin. Check:
```python
print(user.is_superuser)  # Should be True
print(user.role)  # Should be 'admin'
```

---

## Performance Notes

- Database queries use indexes for fast lookups
- Encryption/decryption cached in memory during sync
- Bulk certificate processing with transaction support
- Risk scoring integrated for immediate assessment
- Audit logging async-ready (can be moved to Celery)

---

## Security Checklist

- [x] Passwords never stored in plaintext
- [x] Encryption uses AES-256-GCM
- [x] PBKDF2 with 100,000 iterations for key derivation
- [x] Access control enforced (superadmin/admin only)
- [x] IP address and user tracking
- [x] Audit trail for all operations
- [x] SSL/TLS support for WinRM
- [x] Certificate verification options
- [x] CSRF protection via DRF
- [x] SQL injection prevention via ORM

---

## Version Information

- Django: 5.2.13
- Django REST Framework: Latest
- Cryptography: 46.0.7+
- Python: 3.13+

---

## Support & Documentation

For detailed information, see:
- `AD_CS_IMPLEMENTATION_COMPLETE.md` - Full implementation details
- `api.js` - Frontend API client
- Inline code comments - Each file has comprehensive docstrings

---

**Last Updated**: Today  
**Status**: Production Ready ✅  
**Maintainer**: CertEye Team
