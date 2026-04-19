# CertEye - Quick Start Guide

## What's New

✨ **Brand new HomePage landing page** showing all features and roles
✨ **Role-Based Access Control** with 4 different user roles  
✨ **Admin Panel** for SuperAdmin to manage users and upgrade roles
✨ **Initial SuperAdmin account** ready to use

---

## Quick Start (2 Minutes)

### 1. Start Backend
```bash
cd ssl_backend
source ../venv/bin/activate
python manage.py runserver
```

### 2. Start Frontend (new terminal)
```bash
cd ssl_frontend
npm run dev
```

### 3. Open Browser
Visit: **http://localhost:5173**

---

## Default Credentials

```
SuperAdmin Login:
  Username: superadmin
  Password: SuperAdmin123!
  Role: Super Admin (🟨)
```

---

## Test Flow (5 Minutes)

### Step 1: Home Page
1. You see beautiful landing page
2. Shows all features and role permissions
3. Click "Get Started" or "Sign Up"

### Step 2: Register New User
1. Fill in: username, email, password
2. Click "Create Account"
3. Auto-login and redirected to dashboard
4. Role: **User** 🟦 (can scan domains)

### Step 3: SuperAdmin Upgrades User
1. Logout
2. Login with superadmin
3. Click "👨‍💼 Admin Panel" (golden link in sidebar)
4. Select the user you created
5. Change role to "Admin"
6. Click "Update Role"

### Step 4: Login as Upgraded Admin
1. Logout
2. Login with the user (now Admin 🔴)
3. Notice: More features available
4. Dashboard shows full certificate list
5. Can do everything except manage other users

### Step 5: Test Domain Scanning
1. Enter: "google.com"
2. Click "🔎 Scan"
3. See certificate details in 2-3 seconds
4. Statistics update automatically

---

## User Roles Explained

| Role | Can Do | Cannot Do |
|------|--------|-----------|
| **SuperAdmin** 🟨 | Manage users, upgrade roles, access admin panel, scan domains, view everything | Nothing - full access |
| **Admin** 🔴 | Scan domains, manage certificates, view all data, create alerts | Manage users |
| **User** 🟦 | Scan domains, view own data, see statistics | Create alerts, manage users |
| **Viewer** ⚪ | View certificates (read-only), see reports | Scan domains, manage anything |

---

## Key Files

**Frontend:**
- `src/pages/HomePage.jsx` - Landing page (600+ lines)
- `src/pages/AdminPanelPage.jsx` - Admin interface (300+ lines)
- `src/styles/home.css` - Homepage styling (700+ lines)
- `src/styles/admin-panel.css` - Admin panel styling (400+ lines)

**Backend:**
- `apps/authentication/models.py` - User model with roles
- `apps/authentication/views.py` - User management API
- `apps/authentication/permissions.py` - Role permissions
- `management/commands/create_superadmin.py` - Create superadmin

---

## API Quick Reference

```
GET  /api/auth/profile              → Your user info
POST /api/auth/login                → Login (returns JWT token)
POST /api/auth/logout               → Logout
POST /api/auth/register             → Create new account

// SuperAdmin only:
GET  /api/auth/users                → List all users
POST /api/auth/users/{id}/role      → Change user role

GET  /api/certificates/             → List certificates
POST /api/certificates/scan/        → Scan domain
```

---

## Troubleshooting

**No Admin Panel link?**
- Make sure you're logged in as SuperAdmin
- Refresh page (F5)
- Check browser console for errors

**401 Unauthorized errors?**
- Clear local storage: `localStorage.clear()`
- Log out and log back in
- Refresh page

**Domain scan not working?**
- Make sure backend is running
- Try with "google.com"
- Check Network tab in DevTools

**Styling looks broken?**
- Hard refresh: Ctrl+F5
- Clear browser cache
- Check if frontend is running without errors

---

## Complete Testing

Follow **COMPLETE_TEST_GUIDE.md** for:
- 10 detailed test scenarios
- Step-by-step verification
- Expected results for each test
- Error handling tests
- Performance notes

---

## Features Implemented

✅ Landing page with features overview
✅ 4 user roles with different permissions
✅ Admin panel for user management
✅ User role upgrading system
✅ Domain scanning (all roles)
✅ Real-time statistics
✅ Dark amethyst theme throughout
✅ JWT authentication
✅ Protected routes
✅ Responsive design
✅ Comprehensive API

---

## Next Steps

1. Test the home page
2. Register a test user
3. Login as SuperAdmin
4. Use Admin Panel to upgrade user
5. Test with different roles
6. Scan some domains
7. Verify all permissions working

---

## Success Indicators

✅ Home page loads beautifully
✅ Can register and login
✅ SuperAdmin can see Admin Panel
✅ Can update user roles
✅ Domain scanning works
✅ Statistics display correctly
✅ No 401 unauthorized errors
✅ All theme colors applied

---

**Ready to go!** Visit http://localhost:5173
