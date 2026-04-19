# 🚀 How to Run CertEye - Backend & Frontend

## ⚡ Super Quick Start (5 minutes)

### Terminal 1: Backend
```bash
cd ssl_backend
python manage.py runserver
```

**Expected output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### Terminal 2: Frontend
```bash
cd ssl_frontend
npm install    # First time only
npm run dev
```

**Expected output:**
```
VITE v4.5.0 ready in 250 ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

### Open in Browser
- Frontend: **http://localhost:5173/**
- Backend API: **http://localhost:8000/api/**
- Admin: **http://localhost:8000/admin/**

---

## 📋 First Time Complete Setup

### Step 1: Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd ssl_backend

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create admin user (follow prompts)
python manage.py createsuperuser
# Enter: username (e.g., admin)
# Enter: email (e.g., admin@example.com)
# Enter: password
# Enter: password again

# Start Django development server
python manage.py runserver

# Terminal will show:
# Starting development server at http://127.0.0.1:8000/
```

✅ **Backend running on http://localhost:8000**

---

### Step 2: Frontend Setup (Terminal 2 - NEW TERMINAL)

```bash
# Navigate to frontend folder
cd ssl_frontend

# Install Node.js dependencies (first time only)
npm install
# This may take 1-2 minutes...

# Start Vite development server
npm run dev

# Terminal will show:
# VITE vX.X.X ready in XXX ms
# ➜  Local:   http://localhost:5173/
```

✅ **Frontend running on http://localhost:5173**

---

## 🌐 Access the Application

| Component | URL | Credentials |
|-----------|-----|-------------|
| Frontend | http://localhost:5173/ | admin / password |
| API Docs | http://localhost:8000/api/ | JWT token required |
| Admin Panel | http://localhost:8000/admin/ | admin / password |

---

## 🧪 Test Certificate Scanning

### Method 1: Command Line (Easiest)

```bash
cd ssl_backend
python manage.py scan_certificates google.com
```

**Output:**
```
📡 Starting certificate scan at 2026-04-17T14:30:00+00:00

✨ Created: google.com
   ├─ Subject:     CN=google.com, O=Google LLC, C=US
   ├─ Issuer:      CN=Google Internet Authority G3
   ├─ Key Length:  2048 bits
   ├─ Days Left:   283
   ├─ Risk Level:  low (10/100)
   └─ Type:        single

✅ Scan completed at 2026-04-17T14:30:02+00:00
```

---

### Method 2: REST API

```bash
# 1. Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }' | jq .

# Response:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }

# 2. Scan a domain
TOKEN="your-access-token"
curl -X POST http://localhost:8000/api/certificates/scan/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "google.com",
    "timeout": 10
  }' | jq .

# 3. Get all certificates
curl -X GET "http://localhost:8000/api/certificates/" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

### Method 3: Admin Panel

1. Open http://localhost:8000/admin/
2. Login with credentials:
   - Username: `admin`
   - Password: Your password from setup
3. Click **Certificates** in the sidebar
4. View all scanned certificates with:
   - ✅ Color-coded risk levels
   - ✅ Expiration status indicators
   - ✅ Search and filtering
   - ✅ Certificate details

---

### Method 4: Frontend UI

1. Open http://localhost:5173/
2. Click **Login**
3. Enter credentials:
   - Username: `admin`
   - Password: Your password from setup
4. Navigate to **Certificates** page
5. Click **Scan Certificate**
6. Enter domain name and click **Scan**

---

## 📊 Expected Data Flow

```
User Input (Domain: google.com)
         ↓
    [Frontend]
    Sends HTTP request to /api/certificates/scan/
         ↓
    [Backend]
    Receives request, validates JWT token
         ↓
    [Certificate Service]
    ├─ Fetcher: Connect to google.com:443
    ├─ Parser: Extract certificate data
    ├─ Risk Engine: Calculate risk score
    └─ ORM: Store in database
         ↓
    [Response]
    Returns certificate object with all data
         ↓
    [Frontend]
    Displays in dashboard/certificate list
```

---

## 🔧 Common Issues & Fixes

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'django'`
```bash
# Fix: Install dependencies
cd ssl_backend
pip install -r requirements.txt
```

**Error**: `django.db.utils.OperationalError: no such table`
```bash
# Fix: Run migrations
python manage.py migrate
```

**Error**: `Address already in use: port 8000`
```bash
# Fix: Use different port
python manage.py runserver 8001
```

---

### Frontend Won't Start

**Error**: `npm: command not found`
```bash
# Fix: Install Node.js
# Download from https://nodejs.org/
# Then verify: node --version
```

**Error**: `npm ERR! code EACCES`
```bash
# Fix: Fix npm permissions
sudo chown -R $(whoami) ~/.npm
```

---

### Certificate Scanning Fails

**Error**: `DNSResolutionError: Failed to resolve domain`
```bash
# Fix: Check domain spelling and internet
ping google.com
```

**Error**: `ConnectionTimeoutError: timed out after 10s`
```bash
# Fix: Increase timeout
python manage.py scan_certificates google.com --timeout 30
```

---

## 📝 Useful Commands

### Backend Commands

```bash
cd ssl_backend

# Start dev server
python manage.py runserver

# Run system checks
python manage.py check

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Scan domain
python manage.py scan_certificates google.com

# Scan with verbose output
python manage.py scan_certificates google.com --verbose

# Scan multiple domains
python manage.py scan_certificates google.com github.com amazon.com

# Custom timeout
python manage.py scan_certificates google.com --timeout 15

# Don't update existing
python manage.py scan_certificates google.com --no-update
```

### Frontend Commands

```bash
cd ssl_frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🔗 Important URLs

| Purpose | URL |
|---------|-----|
| **Frontend** | http://localhost:5173/ |
| **API Base** | http://localhost:8000/api/ |
| **Admin Panel** | http://localhost:8000/admin/ |
| **Scan Endpoint** | http://localhost:8000/api/certificates/scan/ |
| **List Certificates** | http://localhost:8000/api/certificates/ |

---

## 📊 API Response Example

**Request:**
```bash
POST /api/certificates/scan/
{
  "domain": "google.com",
  "timeout": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Certificate for google.com created successfully",
  "status": "created",
  "certificate": {
    "id": 1,
    "domain": "google.com",
    "certificate_type": "single",
    "issuer": "CN=Google Internet Authority G3, O=Google Trust Services LLC, C=US",
    "subject": "CN=google.com, O=Google LLC, C=US",
    "serial_number": "abc123def456",
    "signature_algorithm": "sha256WithRSAEncryption",
    "key_length": 2048,
    "valid_from": "2026-01-15T00:00:00Z",
    "valid_to": "2027-01-15T00:00:00Z",
    "days_remaining": 283,
    "risk_level": "low",
    "risk_score": 10,
    "source_type": "scanner",
    "status": "active",
    "last_scanned": "2026-04-17T14:30:00Z",
    "created_at": "2026-04-17T14:30:00Z",
    "updated_at": "2026-04-17T14:30:00Z"
  },
  "error": null
}
```

---

## ✅ Verification Checklist

Before you start, verify:

- [ ] Python 3.8+ installed: `python --version`
- [ ] Node.js 16+ installed: `node --version`
- [ ] npm installed: `npm --version`
- [ ] Virtual environment has dependencies: `pip list | grep Django`
- [ ] Backend requirements installed: `pip install -r ssl_backend/requirements.txt`
- [ ] Database migrated: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`

---

## 🎯 Typical Development Session

```bash
# Terminal 1: Backend
cd ssl_backend
python manage.py runserver
# Runs until you press Ctrl+C

# Terminal 2: Frontend
cd ssl_frontend
npm run dev
# Runs until you press Ctrl+C

# Terminal 3: Testing (optional)
cd ssl_backend
python manage.py scan_certificates google.com
```

Browser shows:
- Frontend at http://localhost:5173/
- Admin at http://localhost:8000/admin/

---

## 📚 Documentation Reference

For more details, see:
- `QUICK_START.md` - 5-minute overview
- `STARTUP_GUIDE.md` - Detailed setup guide
- `CERTIFICATE_SERVICE_QUICK_REF.md` - API reference
- `ssl_backend/apps/certificates/README.md` - Service docs

---

## 🎉 That's It!

You now have:
- ✅ Django backend running
- ✅ React frontend running
- ✅ Certificate scanning service
- ✅ Admin panel
- ✅ REST API
- ✅ Authentication

**Happy certificate scanning! 🎉**
