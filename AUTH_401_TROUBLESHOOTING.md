# 401 Unauthorized Error - Troubleshooting Guide

## Problem Summary
You're receiving 401 (Unauthorized) errors when trying to access the API endpoints from the frontend. This means the JWT token is either:
1. Not being sent to the backend
2. Invalid or expired
3. The frontend is not authenticated yet

## Root Causes Identified & Fixed

### 1. ✅ FIXED: API Base URL Not Set
**Problem**: Frontend didn't know where to send API requests
**Solution**: Created `.env` file with `VITE_API_BASE=http://localhost:8000`

### 2. ✅ FIXED: No Authentication Protection
**Problem**: Users could access protected pages without logging in
**Solution**: Added `ProtectedRoute` component in `App.jsx` that checks authentication before allowing access

### 3. ✅ FIXED: Missing Error Handling
**Problem**: No clear feedback when authentication failed
**Solution**: Added error messages and loading states to Dashboard

### 4. ✅ FIXED: JWT Token Not Persisting
**Problem**: Token might not be properly stored after login
**Solution**: Improved API interceptor with logging and better error handling

## Step-by-Step Fix

### Step 1: Clear Browser Storage
1. Open DevTools (F12)
2. Go to Application tab → Local Storage
3. Delete all entries for localhost:5173
4. Clear cookies for localhost:5173

### Step 2: Restart Backend
```bash
# Kill existing process
lsof -i :8000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null

# Start backend
cd ssl_backend
source ../venv/bin/activate
python manage.py runserver
```

### Step 3: Restart Frontend
```bash
# Kill existing npm process (Ctrl+C in terminal or)
killall node 2>/dev/null

# Start frontend
cd ssl_frontend
npm run dev
```

### Step 4: Test Login Flow
1. Visit `http://localhost:5173/login`
2. Click "Sign Up" tab
3. Enter credentials:
   - Username: testuser123
   - Email: test@example.com
   - Password: TestPass123!
4. Click "Create Account"
5. Check browser console (F12) for logs starting with `[API]`

## Debugging Checklist

### In Browser Console (F12)
```javascript
// Check if token exists
localStorage.getItem('access_token')
// Should return: "eyJ0eXAiOiJKV1QiLCJhbGc..." (long string)

// Check backend API
fetch('http://localhost:8000/api/certificates/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  }
}).then(r => r.json()).then(console.log)
```

### In Backend (Terminal)
```bash
# Check if backend is running
curl -X GET http://localhost:8000/api/certificates/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json"

# Response should be 200 OK with certificate list
```

## Common Issues & Solutions

### Issue 1: Token Not In Local Storage After Login
**Symptom**: Login succeeds but token not saved
**Solution**:
```javascript
// Check auth.js login response
// Make sure it stores both 'access' and 'refresh' tokens
localStorage.setItem('access_token', response.data.access)
localStorage.setItem('refresh_token', response.data.refresh)
```

### Issue 2: CORS Error (401 from preflight)
**Symptom**: Seeing OPTIONS request fail in Network tab
**Solution**:
```python
# Verify CORS settings in Django settings.py
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173'
]
```

### Issue 3: Token Expired (401 after working before)
**Symptom**: Was working, then suddenly 401 errors
**Solution**:
1. Clear local storage: `localStorage.clear()`
2. Log out and log back in
3. Token should be refreshed

### Issue 4: Backend Not Accepting Token
**Symptom**: Valid token but still 401
**Solution**:
```python
# Check JWT settings in settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## Network Tab Inspection

### What You Should See:

**1. Login Request (POST /api/auth/login)**
```
Status: 200 OK
Response Headers:
  Content-Type: application/json

Response Body:
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

**2. Subsequent Requests (GET /api/certificates/)**
```
Status: 200 OK
Request Headers:
  Authorization: Bearer eyJ0eXAiOiJKV1Q...
  
Response Body:
{
  "count": 9,
  "results": [...]
}
```

## Backend Configuration Files

### ✅ Created: `.env`
```dotenv
DJANGO_SECRET_KEY=ssl-lifecycle-secret-key-change-in-production
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=*,localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=true
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### ✅ Created: `ssl_frontend/.env`
```dotenv
VITE_API_BASE=http://localhost:8000
```

## Frontend Changes Made

### ✅ Updated: `api.js`
- Added proper base URL: `http://localhost:8000`
- Added request interceptor logging
- Added response interceptor for 401 errors
- Clear tokens on 401 to force re-login

### ✅ Updated: `App.jsx`
- Added `ProtectedRoute` component
- Checks authentication before showing dashboard
- Redirects to login if not authenticated

### ✅ Updated: `DashboardPage.jsx`
- Added error state display
- Added loading state messages
- Added detailed console logging
- Better error messages

## Testing the Fix

### Test 1: Fresh Registration
```
1. Clear local storage (Ctrl+Shift+Del)
2. Visit http://localhost:5173
3. Should redirect to /login
4. Click "Sign Up"
5. Fill form and submit
6. Should redirect to /dashboard
7. Check console for [API] logs
```

### Test 2: Certificate Scanning
```
1. On dashboard, enter "google.com"
2. Click "Scan"
3. Should show result in 2-3 seconds
4. Check Network tab for POST /api/certificates/scan/
5. Response should be 200 OK with certificate data
```

### Test 3: Token Refresh
```
1. Log in successfully
2. Wait 15+ minutes (token typically lasts 5-60 minutes)
3. Try to access dashboard
4. System should automatically refresh token
5. Or redirect to login if refresh fails
```

## Files Modified

✅ `ssl_frontend/src/api.js` - Added base URL + logging
✅ `ssl_frontend/src/App.jsx` - Added ProtectedRoute
✅ `ssl_frontend/src/pages/DashboardPage.jsx` - Added error handling
✅ `ssl_frontend/.env` - Created with API base URL
✅ `ssl_backend/.env` - Created with proper config

## Quick Resolution Steps

If still getting 401 errors after fixes:

1. **Hard refresh browser**: Ctrl+F5 (or Cmd+Shift+R on Mac)
2. **Clear service workers**: DevTools → Application → Service Workers → Unregister
3. **Check backend logs**: Look for authentication errors in terminal
4. **Check CORS headers**: Use Network tab → Response Headers
5. **Test with curl**: Verify backend works with direct HTTP request

## Expected Success Indicators

✅ Browser console shows `[API] POST http://localhost:8000/api/auth/login - Token: Present`
✅ LocalStorage contains `access_token` with long JWT string
✅ Dashboard loads without error
✅ Can scan domains and see results
✅ Statistics update in real-time
✅ No more 401 errors

## Need More Help?

Check these locations for errors:
1. **Browser Console** (F12) - JavaScript errors
2. **Network Tab** (F12) - HTTP status codes and headers
3. **Backend Terminal** - Django error messages
4. **Local Storage** (F12 → Application) - Token storage

