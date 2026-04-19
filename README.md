# 🔐 CertEye - Centralized Internal PKI Certificate Lifecycle Management System

## ✅ Migration Notice (React + Django + PostgreSQL)

This repository is being migrated to a **React + Django (DRF) + PostgreSQL** stack. The new backend lives in `backend/` and the new frontend lives in `frontend/`. The legacy Flask content below remains for reference only.

### New Stack Quick Start

**Backend (Django + PostgreSQL)**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

export POSTGRES_DB=certeye
export POSTGRES_USER=certeye
export POSTGRES_PASSWORD=certeye_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

python backend/manage.py makemigrations certificates
python backend/manage.py migrate
python backend/manage.py runserver 8000
```

**Frontend (React)**

```bash
cd frontend
npm install
npm run dev
```

Dashboard: `http://localhost:5173` (API on `http://localhost:8000`).

---

A lightweight web-based system for managing internal PKI certificates, monitoring expiration dates, and generating alerts before certificates expire. Built with Flask and SQLite.

## 📋 Features

- **Certificate Ingestion**: REST API to receive certificate data from PowerShell agents
- **Expiration Monitoring**: Automatically calculates days to expiry and assigns risk levels
- **Risk Assessment**: Three-tier risk classification (CRITICAL ≤15 days, HIGH ≤30 days, NORMAL >30 days)
- **Dashboard**: Clean Bootstrap-based web interface showing certificate statistics and status
- **Alert API**: Dedicated endpoint for retrieving certificates expiring within a threshold
- **SQLite Database**: Simple local database, easily upgradeable to PostgreSQL
- **RESTful API**: Well-documented endpoints for programmatic access

## 🏗️ Project Structure

```
CertEye/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── certeye.db                  # SQLite database (created on first run)
├── add_sample_data.py          # Script to populate test data
├── POWERSHELL_EXAMPLES.md      # PowerShell agent integration guide
├── README.md                   # This file
├── models/
│   ├── __init__.py            # Database initialization
│   └── certificate.py         # Certificate model with risk logic
├── routes/
│   ├── __init__.py            # Routes package
│   └── api.py                 # REST API endpoints
├── templates/
│   └── dashboard.html         # Web dashboard (Bootstrap 5)
└── static/                    # Static files (CSS, JS, images)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation & Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd /home/sasmitha/Sharewindows11/SlIIT/ISP/CertEye
   ```

2. **Create a Python virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database** (optional - created automatically on first run):
   ```bash
   python app.py
   # Press Ctrl+C to stop
   ```

5. **Add sample test data** (optional):
   ```bash
   python add_sample_data.py
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the dashboard**:
   - Open your browser and navigate to: **http://localhost:5000**
   - You should see the CertEye dashboard with certificate statistics

## 📡 REST API Endpoints

### 1. Receive Certificate Data (PowerShell Agent)

**POST** `/api/internal-certificates`

Accepts certificate data from PowerShell agent and stores it in the database.

**Request Body** (JSON):
```json
{
    "server_name": "SERVER01",
    "subject": "CN=server01.corp.local",
    "issuer": "CN=Corp Issuing CA",
    "thumbprint": "ABC123DEF456789012345678901234567890ABCD",
    "expiry_date": "2025-12-31T23:59:59Z",
    "certificate_template": "WebServer"
}
```

**Response** (201 Created):
```json
{
    "success": true,
    "message": "Certificate stored successfully",
    "certificate": {
        "id": 1,
        "server_name": "SERVER01",
        "subject": "CN=server01.corp.local",
        "issuer": "CN=Corp Issuing CA",
        "thumbprint": "ABC123DEF456789012345678901234567890ABCD",
        "expiry_date": "2025-12-31T23:59:59+00:00",
        "certificate_template": "WebServer",
        "days_to_expiry": 315,
        "risk_level": "NORMAL",
        "is_expired": false,
        "expiry_status": "Expires in 315 days",
        "created_at": "2024-03-19T10:30:00",
        "updated_at": "2024-03-19T10:30:00"
    }
}
```

### 2. Get All Certificates

**GET** `/api/certificates`

Retrieve all stored certificates with optional filtering and sorting.

**Query Parameters**:
- `risk_level`: Filter by risk level (NORMAL, HIGH, CRITICAL, EXPIRED)
- `hostname`: Filter by server name (contains match)
- `expired_only`: Only include expired certificates (`true`/`false`)
- `expiring_days`: Include certificates expiring within N days (e.g., 7, 15, 30)
- `search`: Search by thumbprint or subject (partial match)
- `sort_by`: Sort by field (expiry_date, server_name, risk_level, days_to_expiry) - default: expiry_date
- `order`: Sort order (asc, desc) - default: asc

**Examples**:
```bash
# Get all certificates sorted by expiry date
curl http://localhost:5000/api/certificates

# Get only critical certificates
curl http://localhost:5000/api/certificates?risk_level=CRITICAL

# Get certificates sorted by risk level (most critical first)
curl http://localhost:5000/api/certificates?sort_by=risk_level&order=desc

# Get all certificates sorted by days to expiry
curl http://localhost:5000/api/certificates?sort_by=days_to_expiry&order=asc

# Filter by hostname
curl http://localhost:5000/api/certificates?hostname=SERVER01

# Expiring within 15 days
curl http://localhost:5000/api/certificates?expiring_days=15

# Expired only
curl http://localhost:5000/api/certificates?expired_only=true

# Search by thumbprint or subject
curl http://localhost:5000/api/certificates?search=ABC123
```

**Response** (200 OK):
```json
{
    "success": true,
    "count": 8,
    "certificates": [
        {
            "id": 1,
            "server_name": "SERVER01",
            "subject": "CN=server01.corp.local",
            ...
        }
    ]
}
```

### 3. Get Alerts (Expiring Soon)

**GET** `/api/alerts`

Retrieve certificates expiring within a specified threshold (useful for monitoring).

**Query Parameters**:
- `days`: Number of days to check (default: 30)
- `sort_by`: Sort by field (expiry_date, server_name) - default: expiry_date

**Examples**:
```bash
# Get certificates expiring in next 30 days
curl http://localhost:5000/api/alerts

# Get certificates expiring in next 60 days
curl http://localhost:5000/api/alerts?days=60

# Get alerts sorted by server name
curl http://localhost:5000/api/alerts?sort_by=server_name
```

**Response** (200 OK):
```json
{
    "success": true,
    "count": 3,
    "threshold_days": 30,
    "certificates": [
        {
            "id": 1,
            "server_name": "SERVER03",
            "days_to_expiry": 5,
            "risk_level": "CRITICAL",
            ...
        }
    ]
}
```

### 4. Get Single Certificate

**GET** `/api/certificate/<id>`

Retrieve details for a specific certificate by ID.

```bash
curl http://localhost:5000/api/certificate/1
```

### 5. Delete Certificate

**DELETE** `/api/certificate/<id>`

Remove a certificate from the database.

```bash
curl -X DELETE http://localhost:5000/api/certificate/1
```

### 6. Health Check

**GET** `/api/health`

Check if the API is running.

```bash
curl http://localhost:5000/api/health
```

### 7. Dashboard Statistics

**GET** `/api/dashboard-stats`

Get statistics for the dashboard (total count, by risk level, expiring soon).

```bash
curl http://localhost:5000/api/dashboard-stats
```

## 🎯 Risk Level Classification

Certificates are automatically classified based on days remaining until expiration:

| Risk Level | Days to Expiry | Action Required |
|-----------|----------------|-----------------|
| **NORMAL** | > 30 days | Routine management |
| **HIGH** | 16-30 days | Plan remediation |
| **CRITICAL** | ≤ 15 days | Immediate action needed |
| **EXPIRED** | < 0 days | Certificate has expired |

## 💾 Database Schema

### Certificates Table

```sql
CREATE TABLE certificates (
    id INTEGER PRIMARY KEY,
    server_name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    issuer VARCHAR(255) NOT NULL,
    thumbprint VARCHAR(40) UNIQUE NOT NULL,
    expiry_date DATETIME NOT NULL,
    certificate_template VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔗 PowerShell Integration

See **POWERSHELL_EXAMPLES.md** for detailed PowerShell agent integration guide and scripts.

Quick example:

```powershell
# Send certificate data to CertEye
$payload = @{
    server_name = $env:COMPUTERNAME
    subject = $cert.Subject
    issuer = $cert.Issuer
    thumbprint = $cert.Thumbprint
    expiry_date = $cert.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    certificate_template = "WebServer"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/internal-certificates" `
    -Method POST `
    -ContentType "application/json" `
    -Body $payload
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Risk level thresholds (in days)
RISK_LEVEL_CRITICAL = 15  # <= 15 days = CRITICAL
RISK_LEVEL_HIGH = 30       # <= 30 days = HIGH

# Database location
SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR}/certeye.db"

# Application debug mode
DEBUG = True  # Set to False in production
```

## 🔄 Upgrading to PostgreSQL

To use PostgreSQL instead of SQLite:

1. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `config.py`:
   ```python
   SQLALCHEMY_DATABASE_URI = "postgresql://user:password@localhost:5432/certeye"
   ```

3. Run the application to initialize the database schema automatically.

## 🧪 Testing

### Test with curl

```bash
# 1. Add a test certificate
curl -X POST http://localhost:5000/api/internal-certificates \
  -H "Content-Type: application/json" \
  -d '{
    "server_name": "TEST-SERVER",
    "subject": "CN=test.corp.local",
    "issuer": "CN=Test CA",
    "thumbprint": "AABBCCDDEEFF00112233445566778899AABBCCDD",
    "expiry_date": "2025-06-30T23:59:59Z",
    "certificate_template": "WebServer"
  }'

# 2. Get all certificates
curl http://localhost:5000/api/certificates

# 3. Get alerts
curl http://localhost:5000/api/alerts

# 4. Check health
curl http://localhost:5000/api/health
```

### Run Sample Data

```bash
python add_sample_data.py
```

This will populate the database with 8 sample certificates with various expiry dates for testing.

## 📝 Sample Data Included

The `add_sample_data.py` script creates certificates with:
- **CRITICAL risk**: 2 certificates (5, 10 days to expiry)
- **HIGH risk**: 2 certificates (20, 25 days to expiry)
- **NORMAL risk**: 3 certificates (45, 150, 365 days to expiry)
- **EXPIRED**: 1 certificate (2 days past expiry)

## 🛠️ Development Tips

### Enable Debug Mode

Set environment variable before running:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### View Database Contents

```bash
sqlite3 certeye.db
sqlite> SELECT * FROM certificates;
sqlite> .exit
```

### Check Logs

Flask logs API requests by default. Monitor output for errors and integration issues.

## 📦 Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production` in `config.py`
- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Use PostgreSQL instead of SQLite
- [ ] Run behind a reverse proxy (nginx, Apache)
- [ ] Enable HTTPS/SSL
- [ ] Consider adding authentication (Phase 2)
- [ ] Set up automated backups for database
- [ ] Monitor disk space (SQLite can grow large over time)

### Example systemd Service

Create `/etc/systemd/system/certeye.service`:

```ini
[Unit]
Description=CertEye Certificate Lifecycle Manager
After=network.target

[Service]
Type=simple
User=certeye
WorkingDirectory=/opt/certeye
ExecStart=/opt/certeye/venv/bin/python /opt/certeye/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable certeye
sudo systemctl start certeye
```

## 🐛 Troubleshooting

### Database Locked Error

If you see "database is locked", another instance is running. Stop it:

```bash
pkill -f "python app.py"
```

### Port Already in Use

If port 5000 is busy, run on a different port:

```bash
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

### Import Errors

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Timezone Issues

All dates are stored in UTC internally. The API returns ISO 8601 format with timezone information.

## 📊 Future Enhancements (Phase 2+)

- [ ] Authentication & API keys
- [ ] Email/webhook alerts for expiring certificates
- [ ] Scheduled background tasks
- [ ] Certificate renewal tracking
- [ ] Advanced filtering & search
- [ ] Audit trail of changes
- [ ] LDAP/AD integration
- [ ] Certificate issuer management
- [ ] Multi-site support

## 📄 License

Internal use only.

## 👤 Support

For issues or questions, contact the infrastructure team.

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Status**: Production Ready
