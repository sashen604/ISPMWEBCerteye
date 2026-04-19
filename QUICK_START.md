# 🚀 CertEye - Quick Start Commands

## ⚡ Start Everything (5 Minutes)

### Terminal 1: Backend
```bash
cd ssl_backend
python manage.py runserver
```
✅ Runs on: http://localhost:8000

### Terminal 2: Frontend  
```bash
cd ssl_frontend
npm install  # First time only
npm run dev
```
✅ Runs on: http://localhost:5173

### Access Points
- **Frontend**: http://localhost:5173/
- **Backend API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/

---

## 🔑 First Time Setup

```bash
# 1. Go to backend
cd ssl_backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create admin user
python manage.py createsuperuser

# 5. Run server
python manage.py runserver
```

**In another terminal:**
```bash
# 1. Go to frontend
cd ssl_frontend

# 2. Install dependencies
npm install

# 3. Start dev server
npm run dev
```

---

## 🧪 Test Certificate Scanning

### Via CLI
```bash
cd ssl_backend

# Scan single domain
python manage.py scan_certificates google.com

# Scan multiple domains
python manage.py scan_certificates google.com github.com amazon.com

# With verbose output
python manage.py scan_certificates google.com --verbose

# Custom timeout (15 seconds)
python manage.py scan_certificates google.com --timeout 15
```

### Via API
```bash
# 1. Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' | jq -r .access)

# 2. Scan domain
curl -X POST http://localhost:8000/api/certificates/scan/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'

# 3. Get all certificates
curl -X GET "http://localhost:8000/api/certificates/" \
  -H "Authorization: Bearer $TOKEN"
```

### Via Admin Panel
1. http://localhost:8000/admin/
2. Login with superuser credentials
3. Click **Certificates** → View all scanned certificates

---

## 📊 API Quick Reference

### Authentication
```bash
# Login
POST /api/auth/login/
Body: {"username": "admin", "password": "pass"}

# Logout
POST /api/auth/logout/
Body: {"refresh": "<refresh-token>"}

# Get Profile
GET /api/auth/profile/
Header: Authorization: Bearer <token>
```

### Certificates
```bash
# List all
GET /api/certificates/
Header: Authorization: Bearer <token>

# List with filters
GET /api/certificates/?domain=google.com&risk_level=high
GET /api/certificates/?expiration_status=expiring_soon&expiring_days=30

# Get one
GET /api/certificates/1/

# Scan single domain
POST /api/certificates/scan/
Body: {"domain": "google.com", "timeout": 10}

# Scan multiple
POST /api/certificates/scan_batch/
Body: {"domains": ["google.com", "github.com"], "timeout": 10}

# Create manually
POST /api/certificates/
Body: {certificate data}

# Update
PUT /api/certificates/1/
Body: {updated fields}

# Delete
DELETE /api/certificates/1/
```

---

## 🔍 Risk Level Guide

```
🔴 CRITICAL (> 70)   - Expires < 7 days OR weak key (< 2048 bits)
🟠 HIGH (> 50)       - Expires < 30 days OR self-signed
🟡 MEDIUM (> 25)     - Expires < 90 days
🟢 LOW (≤ 25)        - Healthy certificate
```

---

## 🐛 Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: django` | `pip install -r ssl_backend/requirements.txt` |
| `no such table` | `cd ssl_backend && python manage.py migrate` |
| `Connection refused :8000` | Port already in use: `python manage.py runserver 8001` |
| `npm not found` | Install Node.js from https://nodejs.org/ |
| `CORS errors` | Already configured - just run both servers |
| `DNSResolutionError` | Check domain spelling: `ping google.com` |
| `ConnectionTimeoutError` | Increase timeout: `--timeout 30` |

---

## 📁 Project Structure

```
CertEye/
├── ssl_backend/           Django backend (port 8000)
│   ├── apps/
│   │   ├── authentication/   JWT login/logout
│   │   ├── certificates/     SSL scanning & storage
│   │   ├── alerts/           Alert system
│   │   ├── risk_engine/      Risk analysis
│   │   └── audit_logs/       Audit trail
│   ├── ssl_lifecycle/        Django settings
│   ├── manage.py
│   └── requirements.txt
│
├── ssl_frontend/          React frontend (port 5173)
│   ├── src/
│   │   ├── pages/            Login, Dashboard, Certificates
│   │   ├── components/       React components
│   │   ├── services/         Auth & API helpers
│   │   └── App.jsx
│   ├── package.json
│   └── venv.config.js
│
├── powershell/            Certificate collector agent
└── venv/                  Python virtual environment
```

---

## 📚 Documentation Files

- `STARTUP_GUIDE.md` - Detailed setup instructions
- `CERTIFICATE_SERVICE_ARCHITECTURE.md` - System architecture & diagrams
- `CERTIFICATE_SERVICE_QUICK_REF.md` - API reference
- `NEW_FOLDER_STRUCTURE.md` - Project structure overview
- `ssl_backend/apps/certificates/README.md` - Certificate service docs

---

## ✨ Features

✅ SSL/TLS certificate scanning from HTTPS domains  
✅ Automatic risk scoring (0-100)  
✅ JWT authentication with login/logout  
✅ RESTful API for certificate management  
✅ Django admin interface with color-coded displays  
✅ Batch certificate scanning  
✅ CLI management commands  
✅ Advanced filtering & search  
✅ Transaction-safe database operations  
✅ Production-ready error handling  

---

## 🎯 Typical Workflow

1. **Start servers** (both terminals)
2. **Login** at http://localhost:5173/
3. **Scan domain** - Use API or CLI
4. **View results** - Dashboard or admin panel
5. **Monitor** - Check expiration dates and risk levels

---

## 📞 Need Help?

- Check `STARTUP_GUIDE.md` for detailed instructions
- See `CERTIFICATE_SERVICE_ARCHITECTURE.md` for system design
- Review API docs: `CERTIFICATE_SERVICE_QUICK_REF.md`
- Backend docs: `ssl_backend/apps/certificates/README.md`

**Happy Certificate Scanning! 🎉**
