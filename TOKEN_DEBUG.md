# Token Error Troubleshooting Guide

## Quick Fixes (Try in Order)

### 1. Clear Browser Storage (FASTEST)
```bash
# Browser DevTools (F12):
# 1. Application tab
# 2. Local Storage
# 3. Delete: access_token, refresh_token
# 4. Refresh page (Ctrl+R)
# 5. Log in again
```

### 2. Test Backend Token Generation
```bash
cd ssl_backend
source venv/bin/activate

# Test login
python manage.py shell
```

```python
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

# Test with existing user
user = authenticate(username='admin', password='your_password')
if user:
    refresh = RefreshToken.for_user(user)
    print(f"Access: {str(refresh.access_token)[:50]}...")
    print(f"Refresh: {str(refresh)[:50]}...")
else:
    print("Authentication failed - check username/password")
```

### 3. Check Token Endpoint Response
```bash
# From your terminal (not inside Python):
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"YOUR_REFRESH_TOKEN_HERE"}'

# You should get:
# {"access":"eyJ0..."}  OR
# {"detail":"Given token not valid..."}
```

### 4. Verify Backend is Running
```bash
# Check if Django is responding
curl http://localhost:8000/api/auth/user/

# Should return 401 (not authenticated) or 200 (if authenticated)
# NOT a connection error like "Connection refused"
```

### 5. Clear Browser Cache + Restart
```bash
# After stopping all browsers:
# Chrome: Settings → Privacy → Clear browsing data → All time
# Firefox: Settings → Privacy → Clear Recent History
# Safari: Develop → Empty Web Storage

# Then restart browser and try login
```

## Common Causes

| Error | Cause | Solution |
|-------|-------|----------|
| "Given token not valid" | Token expired or corrupted | Clear localStorage, log in again |
| 401 on API calls | Access token expired | Wait for auto-refresh or log in |
| 500 on refresh endpoint | Backend error | Check Django logs, restart backend |
| Connection refused | Backend not running | `python manage.py runserver 0.0.0.0:8000` |
| CORS error | Frontend/backend domain mismatch | Check VITE_API_BASE in frontend |

## Debug Console Commands

Open browser DevTools (F12) → Console tab:

```javascript
// Check if tokens exist
console.log("Access:", localStorage.getItem('access_token')?.substring(0, 50) || 'MISSING');
console.log("Refresh:", localStorage.getItem('refresh_token')?.substring(0, 50) || 'MISSING');

// Clear tokens manually
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
console.log("Tokens cleared");

// Test refresh endpoint directly
fetch('http://localhost:8000/api/auth/refresh/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh: localStorage.getItem('refresh_token') })
}).then(r => r.json()).then(d => console.log("Response:", d));
```

## When All Else Fails

```bash
# Backup database
cp ssl_backend/db.sqlite3 ssl_backend/db.sqlite3.backup

# Create new admin user
cd ssl_backend && source venv/bin/activate
python manage.py createsuperuser
# Follow prompts to create user

# Restart backend
python manage.py runserver 0.0.0.0:8000

# Test with new credentials
```

## Prevention

- ✅ Always log out before clearing browser cache
- ✅ Don't manually edit localStorage
- ✅ Keep refresh tokens fresh (7-day lifetime)
- ✅ Use browser's "Save password" feature
- ✅ Test in private/incognito window for clean session

## Getting Help

When reporting token issues, include:

1. Error message from browser console (F12)
2. Backend logs: `tail -50 ssl_backend/logs/*.log` (if logs exist)
3. Django version: `python -c "import django; print(django.__version__)"`
4. Browser type and version: Check in browser DevTools
5. Steps to reproduce the issue
6. Whether it happens on first login or after timeout
