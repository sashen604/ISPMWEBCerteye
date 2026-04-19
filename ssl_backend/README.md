# SSL Certificate Lifecycle Management System - Backend

Production-ready Django REST backend with modular apps for authentication, certificates, alerts, risk engine, and audit logs.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create PostgreSQL database and set environment variables (see `.env.example`).

```bash
export POSTGRES_DB=ssl_lifecycle
export POSTGRES_USER=ssl_user
export POSTGRES_PASSWORD=ssl_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```

Run migrations and start the server:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```

## Apps

- `apps.authentication`
- `apps.certificates`
- `apps.alerts`
- `apps.risk_engine`
- `apps.audit_logs`
