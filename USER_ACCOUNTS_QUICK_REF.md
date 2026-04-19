# Quick Reference - Permanent User Accounts

## Login Credentials

### Superadmin Account
- **Username:** superadmin
- **Password:** Admin@123456
- **Role:** superadmin (Full system access)
- **Email:** superadmin@certeye.local

### Admin Account
- **Username:** admin
- **Password:** Admin@123456
- **Role:** admin (Administrative access)
- **Email:** admin@certeye.local

### Test User Account
- **Username:** testuser
- **Password:** Test@123456
- **Role:** user (Standard user access)
- **Email:** testuser@certeye.local

## API Endpoint

**Login URL:** `http://localhost:8001/api/auth/login`

**Request:**
```json
{
  "username": "superadmin",
  "password": "Admin@123456"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 4,
    "username": "superadmin",
    "email": "superadmin@certeye.local",
    "role": "superadmin",
    "role_display": "Super Admin",
    "is_superadmin": true,
    "is_admin": true,
    "is_active": true
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Database Info

- **Database:** PostgreSQL (ssl_lifecycle)
- **Table:** authentication_user
- **Migration:** apps/authentication/migrations/0004_create_default_users.py

## Status

✅ All accounts created and verified
✅ Passwords validated and working
✅ Accounts persist after backend restart
✅ Ready for use

---

**Note:** These are permanent accounts created via data migration. They will automatically exist whenever the project starts or the database is migrated.
