# CertEye Complete System Test Guide

## System Features Summary

### ✨ What's New
1. **HomePage** - Beautiful landing page showing features, roles, and how it works
2. **Role-Based Access Control** - SuperAdmin, Admin, User, Viewer roles
3. **User Management** - SuperAdmin can upgrade users to different roles
4. **Admin Panel** - Dedicated interface for SuperAdmin to manage users
5. **Full Authentication** - Registration, login, JWT tokens, logout

---

## Initial Setup (Already Complete ✅)

### Backend Services
```bash
# Start backend
cd ssl_backend
source ../venv/bin/activate
python manage.py runserver
```

### Frontend Services
```bash
# Start frontend (in another terminal)
cd ssl_frontend
npm run dev
```

### Database Initialization (Already Done ✅)
- ✅ Created initial superadmin user
- ✅ Applied all migrations
- ✅ User model supports: superadmin, admin, user, viewer

---

## Test Scenario 1: Initial Home Page Load

### Steps:
1. Open browser: **http://localhost:5173**
2. Should see:
   - ✅ Navigation bar with "CertEye" logo
   - ✅ Hero section with "Monitor Your SSL/TLS Certificates"
   - ✅ Features grid (6 feature cards)
   - ✅ Roles section (4 role cards with permissions)
   - ✅ How it works (4-step process)
   - ✅ Get Started button

### Expected Result:
```
✅ HOME PAGE DISPLAYS CORRECTLY
✅ All sections visible
✅ Links are functional
✅ Dark amethyst theme applied throughout
```

---

## Test Scenario 2: Normal User Registration

### Steps:
1. Click "Get Started" or "Sign Up" on home page
2. Fill registration form:
   - **Username**: testuser1
   - **Email**: testuser1@example.com
   - **Password**: TestPass123!
   - **Confirm**: TestPass123!
3. Click "Create Account"

### Expected Result:
```
✅ User account created
✅ Redirected to dashboard
✅ User role is "User" (not Admin)
✅ Can see domain scanner
✅ Can scan domains and view statistics
✅ CANNOT access Admin Panel
```

### User Details:
- Role: **User** 🟦
- Permissions: Scan domains, view own certificates
- Cannot: Manage users, change roles

---

## Test Scenario 3: SuperAdmin Login

### Steps:
1. On home page, click "Sign In"
2. Enter credentials:
   - **Username**: superadmin
   - **Password**: SuperAdmin123!
3. Click "Sign In"

### Expected Result:
```
✅ Login successful
✅ Redirected to dashboard
✅ User role displays "Super Admin" 🟨
✅ See "Admin Panel" link in sidebar (golden color)
✅ Can access all features
```

---

## Test Scenario 4: SuperAdmin Upgrades User to Admin

### Steps:
1. SuperAdmin logged in
2. Click "👨‍💼 Admin Panel" in sidebar
3. Panel loads showing all users
4. Find "testuser1" in the list
5. Click on testuser1 to select
6. Detail panel appears on right
7. Under "Update User Role":
   - Select dropdown: "Admin"
   - Click "Update Role"

### Expected Result:
```
✅ API call: POST /api/auth/users/{id}/role
✅ User role changed from "user" to "admin"
✅ Status shows "Admin" (red badge)
✅ Confirmation message appears
✅ Stats updated
```

### User Details After Upgrade:
- Role: **Admin** 🔴
- Permissions: Full certificate management, cannot manage users
- New capabilities: Create alerts, generate reports

---

## Test Scenario 5: Upgraded Admin Access

### Steps:
1. Log out SuperAdmin
2. Log in as testuser1 (now Admin role)
3. Note changes:

### Expected Changes:
```
✅ Dashboard shows full certificate list
✅ Can scan any domain
✅ Statistics are fully accessible
✅ Sidebar now shows all options
✅ Statistics show more data
✅ BUT: NO Admin Panel link (only SuperAdmin has it)
```

---

## Test Scenario 6: Domain Scanning (All Roles)

### Steps:
1. Log in as any user (User, Admin, or SuperAdmin)
2. On dashboard, find "🔍 Scan Public Domain" section
3. Enter domain: **google.com**
4. Click "🔎 Scan"

### Expected Result:
```
✅ Loading spinner appears
✅ After 2-3 seconds, certificate details shown
✅ Shows: Risk level, Expiry date, Issuer
✅ Statistics update
✅ Certificate added to recent list
✅ No 401 errors
```

### Certificate Data Displayed:
- Domain name
- Risk level (Critical/High/Medium/Low)
- Days until expiration
- Expiry date
- Issuer
- Risk emoji

---

## Test Scenario 7: Multiple Users & Role Management

### Steps:
1. Register 3 more test users:
   - testuser2 (Email: test2@test.com)
   - testuser3 (Email: test3@test.com)
   - testuser4 (Email: test4@test.com)
2. Log in as SuperAdmin
3. Go to Admin Panel
4. Upgrade each user to different roles:
   - testuser2 → Admin
   - testuser3 → Viewer
   - testuser4 → User

### Admin Panel Should Show:
```
✅ All users listed (5 total: 1 SuperAdmin + 4 regular)
✅ Filter by role works
✅ Role badges with correct colors
✅ Statistics updated
✅ Each user can be selected and modified
```

---

## Test Scenario 8: Authentication Flow

### Test A - Session Persistence
1. Log in as any user
2. Refresh page (F5)
3. Should still be logged in
4. Dashboard loads without 401 errors

### Test B - Token Expiration
1. Logout
2. Try to access /dashboard directly
3. Should redirect to /login

### Test C - CORS & API Integration
1. Open browser DevTools (F12)
2. Go to Network tab
3. Perform action (login, scan, etc.)
4. Check requests:
   - Status: 200 OK (success) or 401 (auth error)
   - Request headers: Authorization header present
   - No CORS errors

---

## Test Scenario 9: Role Permissions Testing

### SuperAdmin Can:
```
✅ View all users
✅ Create users (via registration)
✅ Update user roles
✅ Delete users
✅ Access Admin Panel
✅ Scan domains
✅ View all statistics
✅ See full dashboard
```

### Admin Can:
```
✅ Scan domains
✅ View certificates
✅ See statistics
✅ Create alerts (if implemented)
✅ Generate reports (if implemented)
❌ Cannot access Admin Panel
❌ Cannot manage users
❌ Cannot change roles
```

### User Can:
```
✅ Scan public domains
✅ View own certificates
✅ See basic statistics
❌ Cannot see Admin Panel
❌ Cannot manage users
❌ Cannot change roles
```

### Viewer Can:
```
✅ View certificates (read-only)
✅ View reports (if implemented)
❌ Cannot scan domains
❌ Cannot create alerts
❌ Cannot manage anything
```

---

## Test Scenario 10: Error Handling

### Test A - Invalid Credentials
1. Go to /login
2. Enter wrong password
3. Should see error message: "Invalid credentials"

### Test B - User Already Exists
1. Register with username: "testuser1"
2. Try to register again with same username
3. Should see error: "Username already exists"

### Test C - Missing Required Fields
1. Try to register with empty password
2. Should show: "Password must be at least 8 characters"

### Test D - Network Errors
1. Stop backend server
2. Try to scan domain or access dashboard
3. Should show: "Failed to connect to server"

---

## API Endpoints Reference

### Authentication
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/profile
PUT /api/auth/profile
```

### User Management (SuperAdmin Only)
```
GET /api/auth/users           → List all users
GET /api/auth/users/{id}/     → Get specific user
PATCH /api/auth/users/{id}/   → Update user (status, role)
DELETE /api/auth/users/{id}/  → Delete user
POST /api/auth/users/{id}/role → Update user role
```

### Certificates
```
GET /api/certificates/        → List certificates
POST /api/certificates/scan/  → Scan domain
```

---

## Browser DevTools Debugging

### Check Authentication Token
```javascript
// Open browser console (F12 → Console)
localStorage.getItem('access_token')
// Should return: eyJ0eXAiOiJKV1QiLCJhbGc... (long string)
```

### Check User Profile
```javascript
// In console:
fetch('/api/auth/profile', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
}).then(r => r.json()).then(console.log)
```

### Check Admin Users API
```javascript
// In console (SuperAdmin only):
fetch('/api/auth/users', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
}).then(r => r.json()).then(console.log)
```

---

## Common Issues & Solutions

### Issue: 401 Unauthorized Errors
**Solution:**
1. Clear local storage: `localStorage.clear()`
2. Clear browser cache: Ctrl+Shift+Del
3. Log out and log back in
4. Verify token in localStorage

### Issue: Admin Panel Not Showing
**Solution:**
1. Confirm you're logged in as SuperAdmin
2. Check role: `localStorage.getItem('user_role')`
3. Refresh page
4. Check browser console for errors

### Issue: Domain Scan Not Working
**Solution:**
1. Ensure backend is running: `python manage.py runserver`
2. Check Network tab for actual request/response
3. Try with simple domain: google.com
4. Check for timeout errors in console

### Issue: Page Styling Broken
**Solution:**
1. Hard refresh: Ctrl+F5 (or Cmd+Shift+R on Mac)
2. Clear browser cache
3. Check CSS files loaded in Network tab
4. Verify `npm run dev` running without errors

---

## Success Checklist

- [ ] Home page displays correctly
- [ ] Can register new user
- [ ] Can login with credentials
- [ ] Dashboard loads without 401 errors
- [ ] Can scan domains successfully
- [ ] SuperAdmin can access Admin Panel
- [ ] SuperAdmin can upgrade user to Admin
- [ ] Upgraded user can access new features
- [ ] Role-based access working correctly
- [ ] Domain scanning returns correct data
- [ ] Statistics update in real-time
- [ ] No console errors
- [ ] No 401 Unauthorized errors
- [ ] All buttons and links working
- [ ] Dark amethyst theme applied

---

## Performance Notes

### Expected Load Times
- Home page: < 1 second
- Login: < 1 second
- Dashboard: 1-2 seconds
- Domain scan: 2-3 seconds
- Admin Panel user list: 1 second

### Database Queries
- User registration: 1 query
- Login: 1 query
- Load dashboard: 1-2 queries
- Scan domain: 2-3 queries + external HTTPS

---

## Deployment Checklist

Before going to production:
- [ ] Change Django SECRET_KEY in .env
- [ ] Set DEBUG=false
- [ ] Update ALLOWED_HOSTS
- [ ] Configure HTTPS
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Enable CSRF protection
- [ ] Test all APIs with production URL
- [ ] Set up proper logging
- [ ] Enable rate limiting
- [ ] Configure backup strategy

---

## Contact & Support

For issues or questions:
1. Check browser console (F12)
2. Check backend terminal for errors
3. Review this guide's troubleshooting section
4. Enable verbose logging if needed

---

**Test Guide Created**: April 19, 2026
**System Version**: v1.0.0 with Role-Based Access Control
**Status**: Ready for testing ✅
