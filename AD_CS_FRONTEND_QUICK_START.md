# AD CS Component - 60 Second Setup Guide

## ✅ Already Done For You!

The AD CS component is **fully integrated** into your CertEye frontend.

---

## 🎯 To Access It:

### 1️⃣ Start Backend
```bash
cd ssl_backend
python manage.py runserver 8001
```

### 2️⃣ Start Frontend  
```bash
cd ssl_frontend
npm run dev
```

### 3️⃣ Login
- Go to `http://localhost:5173`
- Username: `superadmin`
- Password: `Admin@123456`

### 4️⃣ Find AD CS Management
**Left Sidebar → Bottom of Admin Section → 🏢 AD CS Management**

Or go directly to: `http://localhost:5173/admin/adcs`

---

## 📍 File Changes

Only **3 lines added**, **3 lines modified**:

### ✏️ `App.jsx`
```jsx
// Added this import
import ADCSManagementPage from './pages/ADCSManagementPage.jsx'

// Added this route (in /admin section)
<Route path="adcs" element={<ADCSManagementPage />} />
```

### ✏️ `AdminLayout.jsx`
```jsx
// Added this menu item
<NavLink className="nav-link admin-link" to="/admin/adcs">
  🏢 AD CS Management
</NavLink>
```

### ✨ `ADCSManagementPage.jsx` (NEW)
```jsx
import ADCSSourceForm from '../components/ADCSSourceForm'
import '../styles/adcs.css'

function ADCSManagementPage() {
  return (
    <div className="page-container">
      <ADCSSourceForm />
    </div>
  )
}

export default ADCSManagementPage
```

---

## 🎨 What You'll See

```
┌─────────────────────────────────────────────────┐
│  📊 Dashboard  🔒 Certs  🏢 Internal          │
│  ⚠️ Alerts  🔔 Int.Alerts  📜 History          │
│                                                 │
│  ─────────── ADMIN PANEL ───────────           │
│  👨‍💼 Admin Panel                                │
│  👥 User Management                            │
│  🏢 AD CS Management  ← CLICK HERE            │
│                                                 │
│  ⚙️ Settings                                   │
└─────────────────────────────────────────────────┘
```

---

## ⚙️ Features

✅ Register AD CS servers  
✅ Test connections  
✅ Manual sync certificates  
✅ View sync history  
✅ Edit configurations  
✅ Delete sources  
✅ Secure credential storage  

---

## 🔐 Who Can Access?

Only **Superadmin** and **Admin** users see:
- 🏢 AD CS Management menu item
- Ability to register/manage AD CS sources

Regular users **cannot** see or access this feature.

---

## 📱 Works On

✅ Desktop  
✅ Tablet  
✅ Mobile (responsive)  

---

## 🎯 You're Good to Go!

No additional setup needed. Just:
1. Start the servers
2. Login as admin
3. Click the menu item
4. Start managing AD CS!

---

## 📚 For More Details

- **Full docs**: `AD_CS_IMPLEMENTATION_COMPLETE.md`
- **Quick ref**: `AD_CS_QUICK_REFERENCE.md`
- **Setup guide**: `FRONTEND_AD_CS_INTEGRATION_GUIDE.md`

---

**Status**: ✅ Ready  
**Version**: 1.0
