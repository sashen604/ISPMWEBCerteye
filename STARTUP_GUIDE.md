# CertEye - Complete Startup Guide

## Project Overview

**CertEye** is a production-grade SSL/TLS Certificate Lifecycle Management System built with:
- **Backend**: Django 5.0+ with DRF (Django REST Framework)
- **Frontend**: React 18+ with Vite
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT with SimpleJWT

## Prerequisites

Ensure you have installed:
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ (for production)
- Git

## Project Structure

```
CertEye/
├── ssl_backend/              Django backend (port 8000)
│   ├── apps/
│   │   ├── authentication/  (JWT auth, user management)
│   │   ├── certificates/    (SSL/TLS scanning & storage)
│   │   ├── alerts/          (Alert management)
│   │   ├── risk_engine/     (Risk analysis)
│   │   └── audit_logs/      (Audit trail)
│   ├── manage.py
│   ├── requirements.txt
│   └── ssl_lifecycle/       (Django project settings)
│
├── ssl_frontend/             React frontend (port 5173)
│   ├── src/
│   │   ├── pages/           (Login, Dashboard, Certificates, etc.)
│   │   ├── components/      (Reusable React components)
│   │   ├── services/        (Auth, API helpers)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── venv.config.js
│
├── powershell/              PowerShell certificate collector agent
└── venv/                    Python virtual environment
```

---

## 🚀 Quick Start (5 minutes)

### Terminal 1: Start Django Backend

```bash
# Navigate to backend
cd ssl_backend

# Run Django development server
python manage.py runserver

# Expected output:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

### Terminal 2: Start React Frontend

```bash
# Navigate to frontend
cd ssl_frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev

# Expected output:
# VITE v... ready in XXX ms
# ➜  Local:   http://localhost:5173/
# ➜  press h to show help
```

### Access the Application

- **Frontend**: http://localhost:5173/
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/

---

## 📝 Complete Setup Instructions

### Step 1: Backend Setup

```bash
# 1. Navigate to backend
cd ssl_backend

# 2. Create .env file (optional, for production settings)
cp .env.example .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser for admin access
python manage.py createsuperuser
# Follow prompts to create admin account

# 6. (Optional) Load sample data
python manage.py shell
# >>> from apps.certificates.models import Certificate
# >>> # Add your own test data

# 7. Start the server
python manage.py runserver
```

### Step 2: Frontend Setup

```bash
# 1. Navigate to frontend
cd ssl_frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Open browser to http://localhost:5173/
```

---

## 🧪 Testing Certificate Scanning

### Option 1: Django Management Command

```bash
cd ssl_backend

# Scan single domain
python manage.py scan_certificates google.com

# Scan multiple domains
python manage.py scan_certificates google.com github.com amazon.com

# With custom timeout (15 seconds)
python manage.py scan_certificates google.com --timeout 15

# Verbose output with details
python manage.py scan_certificates google.com --verbose
```

### Option 2: REST API (cURL)

```bash
# 1. Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' \
  -s | jq .

# Example response:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }

# 2. Scan a domain using the access token
curl -X POST http://localhost:8000/api/certificates/scan/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com", "timeout": 10}' \
  -s | jq .

# 3. Get all certificates
curl -X GET "http://localhost:8000/api/certificates/" \
  -H "Authorization: Bearer <your-access-token>" \
  -s | jq .
```

### Option 3: Django Admin

1. Go to http://localhost:8000/admin/
2. Login with your superuser credentials
3. Navigate to **Certificates** section
4. View, filter, and manage certificates with color-coded displays

---

## 📊 API Endpoints Reference

### Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/logout/` | Logout (blacklist token) |
| GET | `/api/auth/profile/` | Get user profile |

### Certificates

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/certificates/` | List all certificates (with filters) |
| POST | `/api/certificates/` | Create certificate (manual) |
| GET | `/api/certificates/{id}/` | Get single certificate |
| PUT | `/api/certificates/{id}/` | Update certificate |
| DELETE | `/api/certificates/{id}/` | Delete certificate |
| POST | `/api/certificates/scan/` | **Scan single domain** |
| POST | `/api/certificates/scan_batch/` | **Scan multiple domains** |

### Query Filters

```bash
# Filter by domain
GET /api/certificates/?domain=google.com

# Filter by risk level
GET /api/certificates/?risk_level=high

# Filter by expiration status
GET /api/certificates/?expiration_status=expiring_soon&expiring_days=30

# Filter by certificate type
GET /api/certificates/?certificate_type=wildcard

# Combine filters
GET /api/certificates/?domain=example&risk_level=critical&expiration_status=expiring_soon
```

---

## 🔐 Authentication Flow

### 1. Login (Get Tokens)

```bash
POST /api/auth/login/
{
  "username": "admin",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Use Access Token

All subsequent API requests must include:
```
Authorization: Bearer <access-token>
```

### 3. Refresh Token (When Expired)

```bash
POST /api/auth/token/refresh/
{
  "refresh": "<refresh-token>"
}

Response:
{
  "access": "new-access-token..."
}
```

### 4. Logout (Blacklist Token)

```bash
POST /api/auth/logout/
{
  "refresh": "<refresh-token>"
}
```

---

## 🛠️ Development Commands

### Backend Commands

```bash
cd ssl_backend

# Run Django development server
python manage.py runserver

# Run system checks
python manage.py check

# Create migrations for model changes
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Open Django shell (interactive Python)
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Collect static files (production)
python manage.py collectstatic

# Scan domain from CLI
python manage.py scan_certificates google.com --verbose
```

### Frontend Commands

```bash
cd ssl_frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting (if configured)
npm run lint
```

---

## 🗄️ Database Setup

### Development (SQLite - Default)

No setup needed! Django uses SQLite automatically.

```bash
cd ssl_backend
python manage.py migrate
```

### Production (PostgreSQL)

1. **Create PostgreSQL database**

```bash
# Using psql
createuser certeye_user
createdb certeye_db -O certeye_user

# Set password
psql -c "ALTER USER certeye_user WITH PASSWORD 'secure-password';"
```

2. **Update `.env` file**

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://certeye_user:password@localhost:5432/certeye_db
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

3. **Run migrations**

```bash
python manage.py migrate
```

---

## 🔍 Viewing Certificate Data

### Via Django Admin

1. Go to http://localhost:8000/admin/
2. Click **Certificates**
3. View with color-coded displays:
   - 🔴 Red = Critical risk
   - 🟠 Orange = High risk
   - 🟡 Yellow = Medium risk
   - 🟢 Green = Low risk

### Via API

```bash
# Get all certificates (requires login)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/certificates/

# Get specific certificate
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/certificates/1/

# Get expiring certificates
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/certificates/?expiration_status=expiring_soon&expiring_days=30"
```

### Via React Frontend

1. Open http://localhost:5173/
2. Login with credentials
3. Navigate to **Certificates** page
4. View all scanned certificates with filters

---

## 🧬 Risk Scoring Explained

Risk Score (0-100) calculated from:

```
Base: 0

+ Expiration Risk:
  - Expires < 7 days:   +50 ❌
  - Expires < 30 days:  +25 ⚠️
  - Expires < 90 days:  +10 📋
  - Expires ≥ 90 days:  +0  ✅

+ Key Length Risk:
  - < 2048 bits:  +30 ❌
  - < 4096 bits:  +10 📋
  - ≥ 4096 bits:  +0  ✅

+ Certificate Type:
  - Self-signed:  +20 ⚠️
  - Other:        +0  ✅

= Total Risk Score

Risk Levels:
- > 70:  CRITICAL 🔴
- > 50:  HIGH 🟠
- > 25:  MEDIUM 🟡
- ≤ 25:  LOW 🟢
```

---

## 🚨 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'django'`
```bash
# Solution: Install requirements
pip install -r ssl_backend/requirements.txt
```

**Problem**: `django.db.utils.OperationalError: no such table`
```bash
# Solution: Run migrations
cd ssl_backend
python manage.py migrate
```

**Problem**: `Connection refused` on port 8000
```bash
# Solution: Check if port is in use
lsof -i :8000
# Kill existing process and restart
```

### Frontend Issues

**Problem**: `npm: command not found`
```bash
# Solution: Install Node.js from https://nodejs.org/
# Verify installation
node --version
npm --version
```

**Problem**: `npm ERR! code EACCES`
```bash
# Solution: Fix npm permissions
npm install -g npm@latest
```

**Problem**: `CORS errors in browser console`
```bash
# Solution: Backend CORS is configured in ssl_backend/ssl_lifecycle/settings.py
# Make sure frontend URL is in CORS_ALLOWED_ORIGINS
```

### Certificate Scanning Issues

**Problem**: `DNSResolutionError: Failed to resolve domain`
```bash
# Solution: Check domain spelling and internet connection
ping google.com
```

**Problem**: `ConnectionTimeoutError: timed out after 10s`
```bash
# Solution: Increase timeout
python manage.py scan_certificates google.com --timeout 30
```

---

## 📋 Important Files & Configuration

### Backend Configuration

- **Settings**: `ssl_backend/ssl_lifecycle/settings.py`
  - Database configuration
  - JWT settings
  - CORS configuration
  - Installed apps

- **URLs**: `ssl_backend/ssl_lifecycle/urls.py`
  - API routing
  - Admin panel

### Frontend Configuration

- **Vite Config**: `ssl_frontend/vite.config.js`
  - Dev server proxy (forwards `/api` to backend)
  - Build configuration

- **API Client**: `ssl_frontend/src/api.js`
  - Axios configuration
  - JWT token injection
  - Base URL setup

---

## 🔗 Port Configuration

By default:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Frontend API Proxy**: `/api` → `http://localhost:8000/api`

### To change ports:

**Backend** (different port, e.g., 8001):
```bash
python manage.py runserver 8001
```

**Frontend** (different port, e.g., 3000):
```bash
npm run dev -- --port 3000
```

---

## 📦 Dependencies

### Backend (Python)

See `ssl_backend/requirements.txt`:
- Django 5.0+
- Django REST Framework 3.15+
- SimpleJWT (JWT authentication)
- cryptography (SSL certificate handling)
- pyOpenSSL (SSL/TLS operations)
- PostgreSQL driver

### Frontend (Node.js)

See `ssl_frontend/package.json`:
- React 18+
- React Router 6+ (navigation)
- Axios (HTTP client)
- Bootstrap 5 (styling)
- Vite (build tool)

---

## 🚀 Production Deployment

### Backend

```bash
# 1. Set environment variables
export DEBUG=False
export SECRET_KEY=your-production-secret-key
export DATABASE_URL=postgresql://...

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run migrations
python manage.py migrate

# 4. Start with production server (e.g., Gunicorn)
gunicorn ssl_lifecycle.wsgi:application --bind 0.0.0.0:8000
```

### Frontend

```bash
# 1. Build for production
npm run build

# 2. Serve from static directory (typically with Nginx)
# Or deploy to CDN/static hosting service
```

---

## 📞 Support & Documentation

- **Backend Docs**: `ssl_backend/apps/certificates/README.md`
- **Architecture**: `CERTIFICATE_SERVICE_ARCHITECTURE.md`
- **Quick Reference**: `CERTIFICATE_SERVICE_QUICK_REF.md`
- **Project Structure**: `NEW_FOLDER_STRUCTURE.md`

---

## ✅ Quick Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Virtual environment activated
- [ ] Backend requirements installed: `pip install -r ssl_backend/requirements.txt`
- [ ] Frontend dependencies installed: `npm install` (in ssl_frontend)
- [ ] Django migrations run: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`
- [ ] Backend running: `python manage.py runserver`
- [ ] Frontend running: `npm run dev` (in ssl_frontend)
- [ ] Can access http://localhost:5173/
- [ ] Can access http://localhost:8000/admin/
- [ ] Can login with credentials

---

## 🎯 Next Steps

1. **Start Backend**: Open Terminal 1, run `cd ssl_backend && python manage.py runserver`
2. **Start Frontend**: Open Terminal 2, run `cd ssl_frontend && npm run dev`
3. **Create Admin**: Run `python manage.py createsuperuser` (if not done)
4. **Login**: Go to http://localhost:5173/ and login
5. **Scan Certificate**: Use the Certificates page or CLI to scan a domain
6. **View Results**: Check dashboard and admin panel

**Happy Certificate Scanning! 🎉**
