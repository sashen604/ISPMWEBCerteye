# Quick Start - New Certificate Services

## 🚀 Get Started in 5 Minutes

### Step 1: Verify Installation
```bash
cd ssl_backend
source ../venv/bin/activate
python manage.py check
# Expected: System check identified no issues (0 silenced)
```

### Step 2: Start Backend Server
```bash
python manage.py runserver 8001
```

### Step 3: Get Authentication Token

```bash
# Login as admin
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Admin@123456"}'

# Response will include "access" token
# Store it in a variable: TOKEN="your_token_here"
```

---

## 📊 Export Certificates to CSV

### Export All Certificates
```bash
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=all" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificates_all.csv
```

### Export Expiring Certificates (Next 30 days)
```bash
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=expiring&days_threshold=30" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificates_expiring_30d.csv
```

### Export High-Risk Certificates
```bash
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=high_risk&risk_threshold=60" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificates_high_risk.csv
```

### Export Critical Alerts
```bash
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=critical" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificates_critical.csv
```

### Export with Custom Filters
```bash
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=custom&domain_contains=google&risk_level=HIGH&key_length_min=2048" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificates_custom.csv
```

---

## 🚨 Generate Alerts

### Generate All Alerts (Expiry + Crypto Weakness)
```bash
curl -X POST http://localhost:8001/api/alerts/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"alert_type":"both"}'
```

### Generate Only Expiry Alerts
```bash
curl -X POST http://localhost:8001/api/alerts/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"alert_type":"expiry"}'
```

### Generate Only Crypto Weakness Alerts
```bash
curl -X POST http://localhost:8001/api/alerts/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"alert_type":"crypto_weakness"}'
```

### Generate with Custom Thresholds
```bash
curl -X POST http://localhost:8001/api/alerts/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type":"both",
    "custom_thresholds":{
      "CRITICAL":5,
      "HIGH":14,
      "MEDIUM":60
    }
  }'
```

---

## 📋 View Alerts

### Get All Alerts
```bash
curl -X GET http://localhost:8001/api/alerts/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Get Alerts by Severity
```bash
curl -X GET "http://localhost:8001/api/alerts/?severity=CRITICAL" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Get Alert Statistics
```bash
curl -X GET http://localhost:8001/api/alerts/stats/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Get Specific Alert Details
```bash
curl -X GET http://localhost:8001/api/alerts/1/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

## 🧪 Quick Test Scenarios

### Scenario 1: Export Workflow
1. Export all certs
2. Review risk distribution
3. Export high-risk subset
4. Send to security team

```bash
# All certs
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=all" \
  -H "Authorization: Bearer $TOKEN" -o all.csv

# High-risk only
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=high_risk&risk_threshold=70" \
  -H "Authorization: Bearer $TOKEN" -o high_risk.csv

echo "✅ Exports complete - check all.csv and high_risk.csv"
```

### Scenario 2: Alert Generation Workflow
1. Generate alerts
2. Check statistics
3. Review critical alerts
4. Export for report

```bash
# Generate
curl -X POST http://localhost:8001/api/alerts/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"alert_type":"both"}' | python -m json.tool

# Stats
curl -X GET http://localhost:8001/api/alerts/stats/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Export critical
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=critical" \
  -H "Authorization: Bearer $TOKEN" -o critical_alerts.csv
```

---

## 🔧 Python Usage (For Scripts)

### Export Service Example
```python
from apps.certificates.services import CertificateExportService

service = CertificateExportService()

# Export all
filename, content = service.export_all_certificates()
with open(filename, 'wb') as f:
    f.write(content)

# Export expiring within 14 days
filename, content = service.export_expiring_certificates(days_threshold=14)

# Export high-risk (score >= 75)
filename, content = service.export_high_risk_certificates(risk_threshold=75)

# Export critical alerts
filename, content = service.export_critical_alerts()

# Custom filter
filters = {
    'domain_contains': 'google',
    'risk_level': 'CRITICAL',
    'key_length_min': 2048
}
filename, content = service.export_custom_filter(filters)
```

### Alert Engine Example
```python
from apps.alerts.services import AlertEngine

# Default thresholds (CRITICAL:7, HIGH:30, MEDIUM:90 days)
engine = AlertEngine()

# Generate alerts
expiry_alerts = engine.generate_expiry_alerts()
crypto_alerts = engine.generate_crypto_weakness_alerts()

print(f"Generated {len(expiry_alerts)} expiry alerts")
print(f"Generated {len(crypto_alerts)} crypto alerts")

# Custom thresholds
custom_thresholds = {'CRITICAL': 5, 'HIGH': 14, 'MEDIUM': 60}
engine = AlertEngine(expiry_thresholds=custom_thresholds)
alerts = engine.generate_expiry_alerts()
```

---

## 📧 Email Configuration

For alert emails to work, configure SMTP in `.env`:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=alerts@certeye.local
```

---

## ✅ Common Tasks Checklist

- [ ] Export all certificates
- [ ] Export expiring certificates (30 days)
- [ ] Export high-risk certificates
- [ ] Generate all alerts
- [ ] Check alert statistics
- [ ] View critical alerts
- [ ] Export critical alerts to CSV
- [ ] Test custom filters
- [ ] Test email notifications
- [ ] Create daily alert schedule (Celery)

---

## 🐛 Troubleshooting

### "Permission denied" error
→ Ensure you're logged in as admin/superadmin
```bash
# Check user role
curl -X GET http://localhost:8001/api/auth/me/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### "No certificates found" in export
→ Verify certificates exist in database
```bash
# Count certificates
python manage.py shell
from apps.certificates.models import Certificate
Certificate.objects.count()
```

### Email not sending
→ Check email configuration
```bash
# Test email in Django shell
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Testing email', 'test@example.com', ['admin@example.com'])
```

### Filters not working
→ Check parameter syntax
```bash
# URL encode special characters
domain_contains="test.com"
curl -X GET "http://localhost:8001/api/certificates/export_csv/?filter_type=custom&domain_contains=${domain_contains}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Documentation Files

- **Full Implementation**: `IMPLEMENTATION_MISSING_FEATURES_COMPLETE.md`
- **API Documentation**: In this file
- **Code Examples**: `ssl_backend/apps/certificates/tests.py`
- **Inline Docstrings**: In service modules

---

## 🎯 Next Steps

1. **Test the APIs** - Use curl commands above
2. **Review the Code** - Check service modules for details
3. **Run Tests** - `python manage.py test apps.certificates`
4. **Configure Email** - Set up SMTP for notifications
5. **Schedule Alerts** - Set up Celery for daily runs (optional)
6. **Integrate Frontend** - Create React components for export/alerts UI

---

**Status**: ✅ All features working and ready to use!
