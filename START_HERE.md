# CertEye - Start Here! 👋

Welcome to your **Centralized Internal PKI Certificate Lifecycle Management System**!

## ⚡ Quick Links

### 🚀 Get Started (Pick One)

1. **[QUICKSTART.md](QUICKSTART.md)** - 30-second setup guide
2. **[README.md](README.md)** - Full documentation
3. **[POWERSHELL_EXAMPLES.md](POWERSHELL_EXAMPLES.md)** - PowerShell integration

### 📚 Documentation

- **[README.md](README.md)** - Complete API documentation, features, configuration
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide with examples
- **[POWERSHELL_EXAMPLES.md](POWERSHELL_EXAMPLES.md)** - PowerShell agent scripts and examples
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Technical implementation details
- **[PROJECT_MANIFEST.txt](PROJECT_MANIFEST.txt)** - Complete project inventory

## 🚀 Start in 30 Seconds

```bash
cd /home/sasmitha/Sharewindows11/SlIIT/ISP/CertEye
chmod +x run.sh
./run.sh
```

Then visit: **http://localhost:5000**

## 📂 What's Inside

```
CertEye/
├── app.py                           # Flask application
├── config.py                        # Configuration
├── models/certificate.py            # Database model
├── routes/api.py                    # REST API (7 endpoints)
├── templates/dashboard.html         # Bootstrap dashboard
├── add_sample_data.py              # Test data
└── [Documentation files]
```

## 🎯 What It Does

✅ **Receives** certificate data from PowerShell agents  
✅ **Stores** certificates in SQLite database  
✅ **Monitors** expiration dates automatically  
✅ **Calculates** risk levels (CRITICAL/HIGH/NORMAL/EXPIRED)  
✅ **Displays** real-time dashboard with Bootstrap UI  
✅ **Provides** REST API for programmatic access  

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | API health check |
| GET | `/api/certificates` | Get all certificates |
| GET | `/api/alerts` | Get expiring certificates |
| POST | `/api/internal-certificates` | Add/update certificate |
| GET | `/api/dashboard-stats` | Dashboard statistics |

## 🎁 Included

- ✅ 8 sample test certificates (various expiry dates)
- ✅ SQLite database pre-configured
- ✅ Bootstrap 5 dashboard
- ✅ PowerShell integration examples
- ✅ Complete documentation
- ✅ Quick start script

## 🔧 Technology

- **Backend**: Flask 3.0.0
- **Database**: SQLite (PostgreSQL compatible)
- **Frontend**: Bootstrap 5
- **Python**: 3.8+

## 📖 Documentation Guides

### For Users
→ Start with [QUICKSTART.md](QUICKSTART.md)

### For API Integration
→ See [README.md](README.md) - Full API documentation

### For PowerShell Setup
→ See [POWERSHELL_EXAMPLES.md](POWERSHELL_EXAMPLES.md)

### For Technical Details
→ See [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)

## ✨ Key Features

1. **Certificate Ingestion** - REST endpoint accepts PowerShell agent data
2. **Risk Classification** - Automatic categorization (CRITICAL/HIGH/NORMAL/EXPIRED)
3. **Real-time Dashboard** - Bootstrap UI with live statistics
4. **Alert System** - Get certificates expiring within configurable threshold
5. **RESTful API** - 7 endpoints for programmatic access
6. **Sample Data** - 8 test certificates to explore immediately

## 🚀 Next Steps

1. **Start the app**: `./run.sh`
2. **View dashboard**: http://localhost:5000
3. **Test API**: `curl http://localhost:5000/api/health`
4. **Read docs**: Open [README.md](README.md)
5. **Deploy agent**: See [POWERSHELL_EXAMPLES.md](POWERSHELL_EXAMPLES.md)

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: March 19, 2026
