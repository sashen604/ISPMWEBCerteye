# 🚀 PRODUCTION DEPLOYMENT GUIDE - Internal Certificates

## Quick Start for Production

This guide walks you through deploying the Internal Certificate Collection system to production.

---

## Step 1: Prepare Production Environment

### 1.1 Install Database (PostgreSQL Recommended)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql
```

```sql
CREATE DATABASE certeye_prod;
CREATE USER certeye WITH PASSWORD 'your-secure-password';
ALTER ROLE certeye SET client_encoding TO 'utf8';
ALTER ROLE certeye SET default_transaction_isolation TO 'read committed';
ALTER ROLE certeye SET default_transaction_deferrable TO off;
ALTER ROLE certeye SET default_transaction_readonly TO off;
ALTER ROLE certeye SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE certeye_prod TO certeye;
\q
```

### 1.2 Configure Django Settings

Edit `ssl_backend/ssl_lifecycle/settings.py`:

```python
# Production Settings

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'your-ip-address']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'certeye_prod',
        'USER': 'certeye',
        'PASSWORD': 'your-secure-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Redis Cache (for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### 1.3 Install Redis (for Caching/Rate Limiting)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping  # Should return PONG
```

---

## Step 2: Deploy Backend

### 2.1 Clone Repository

```bash
cd /opt
sudo git clone https://your-repo-url/CertEye.git
cd CertEye/ssl_backend
```

### 2.2 Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary django-redis
```

### 2.3 Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2.4 Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 2.5 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

## Step 3: Generate Agent Tokens

Generate tokens for each Windows server that will collect certificates.

```bash
python manage.py shell
```

```python
from apps.certificates.agent_auth import CertificateAgent

# Create agent for each server
servers = [
    'SERVER-01',
    'SERVER-02', 
    'EXCHANGE-01',
    'WEBSERVER-01',
]

for server in servers:
    agent = CertificateAgent.objects.create(
        hostname=server,
        is_active=True
    )
    print(f"{server}: {agent.token}")
    # Save these tokens to secure location!

exit()
```

**Output Example:**
```
SERVER-01: 4c86616af6b96caa1059889b6bf43e14efbacadf
SERVER-02: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
EXCHANGE-01: z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0
WEBSERVER-01: f1e2d3c4b5a6z7y8x9w0v1u2t3s4r5q6p7o8n9m0
```

---

## Step 4: Deploy Frontend

### 4.1 Build Frontend

```bash
cd /opt/CertEye/ssl_frontend
npm install
npm run build
```

### 4.2 Serve Frontend

```bash
# Option 1: Use Nginx to serve static files and proxy API
sudo apt-get install nginx

# Copy build to nginx
sudo cp -r dist/* /var/www/html/

# Configure Nginx proxy_pass to Django backend
# (See Nginx configuration below)

# Option 2: Run with development server (NOT recommended for production)
npm run dev  # Only for testing
```

---

## Step 5: Configure Nginx (Reverse Proxy)

### 5.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/certeye
```

```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Certificate (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    client_max_body_size 100M;
    
    # Static files (Django)
    location /static/ {
        alias /opt/CertEye/ssl_backend/staticfiles/;
        expires 30d;
    }
    
    # Media files
    location /media/ {
        alias /opt/CertEye/ssl_backend/media/;
        expires 7d;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Frontend (React SPA)
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 5.2 Enable Nginx Configuration

```bash
sudo ln -s /etc/nginx/sites-available/certeye /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## Step 6: Run Django with Gunicorn

### 6.1 Install Gunicorn

```bash
source /opt/CertEye/ssl_backend/venv/bin/activate
pip install gunicorn
```

### 6.2 Create Systemd Service

```bash
sudo nano /etc/systemd/system/certeye-django.service
```

```ini
[Unit]
Description=CertEye Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/CertEye/ssl_backend
Environment="PATH=/opt/CertEye/ssl_backend/venv/bin"
ExecStart=/opt/CertEye/ssl_backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/certeye/access.log \
    --error-logfile /var/log/certeye/error.log \
    ssl_lifecycle.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.3 Create Log Directory

```bash
sudo mkdir -p /var/log/certeye
sudo chown www-data:www-data /var/log/certeye
```

### 6.4 Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start certeye-django
sudo systemctl enable certeye-django
sudo systemctl status certeye-django
```

---

## Step 7: Deploy PowerShell Agent to Windows

### 7.1 On Windows Server

```powershell
# Copy PowerShell script
Copy-Item -Path "AutoCollect-CertEye.ps1" -Destination "C:\CertEye\"

# Run collection (test)
C:\CertEye\AutoCollect-CertEye.ps1 `
    -AgentToken "4c86616af6b96caa1059889b6bf43e14efbacadf" `
    -ApiEndpoint "https://your-domain.com/api/certificates/collect_internal/" `
    -Schedule "Daily"
```

### 7.2 Schedule with Windows Task Scheduler

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -File C:\CertEye\AutoCollect-CertEye.ps1 -AgentToken '...' -Schedule 'Scheduled'"

$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

Register-ScheduledTask `
    -TaskName "CertEye-Collect" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest
```

---

## Step 8: Verify Production Setup

### 8.1 Test API Endpoint

```bash
curl -X POST https://your-domain.com/api/certificates/collect_internal/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_token": "your_token_here",
    "hostname": "TEST-SERVER",
    "subject": "test.example.com",
    "issuer": "Test CA",
    "thumbprint": "ABCD1234567890",
    "valid_to": "2025-12-31T23:59:59Z"
  }'
```

Expected Response (200 OK):
```json
{
  "success": true,
  "message": "Certificate created: TEST-SERVER/test.example.com",
  "status": "created",
  "certificate": {
    "id": 1,
    "hostname": "TEST-SERVER",
    "risk_level": "LOW",
    "risk_score": 0,
    "status": "active"
  }
}
```

### 8.2 Check Logs

```bash
# Django errors
tail -f /var/log/certeye/error.log

# Access logs
tail -f /var/log/certeye/access.log

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

### 8.3 Monitor Certificate Collection

```bash
# In Django shell
python manage.py shell
```

```python
from apps.certificates.models import Certificate
from apps.certificates.agent_auth import CertificateAgent, AgentAuditLog

# Check agents
print(CertificateAgent.objects.count(), "agents created")

# Check internal certificates
internal = Certificate.objects.filter(source_type='internal_agent')
print(internal.count(), "internal certificates collected")

# Check audit logs
logs = AgentAuditLog.objects.all().order_by('-created_at')[:10]
for log in logs:
    print(f"{log.created_at}: {log.status} - {log.error_message or 'OK'}")
```

---

## Step 9: Setup SSL Certificate

### 9.1 Use Let's Encrypt (Free)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
sudo certbot renew --dry-run  # Test auto-renewal
```

### 9.2 Or Use Self-Signed (for testing)

```bash
sudo openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout /etc/ssl/private/certeye.key \
    -out /etc/ssl/certs/certeye.crt
```

---

## Step 10: Monitoring & Maintenance

### 10.1 Setup Monitoring

```bash
# Monitor disk space
df -h

# Monitor memory
free -h

# Monitor processes
ps aux | grep gunicorn
ps aux | grep redis

# Monitor database
sudo -u postgres psql certeye_prod -c "SELECT count(*) FROM certificates_certificate;"
```

### 10.2 Backup Database

```bash
# Daily backup
sudo -u postgres pg_dump certeye_prod | gzip > /backup/certeye_$(date +%Y%m%d).sql.gz

# Or add to crontab
0 2 * * * sudo -u postgres pg_dump certeye_prod | gzip > /backup/certeye_$(date +\%Y\%m\%d).sql.gz
```

### 10.3 Rotate Logs

```bash
# Use logrotate
sudo nano /etc/logrotate.d/certeye
```

```
/var/log/certeye/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

---

## Troubleshooting

### Issue: "Cannot connect to database"
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check credentials in settings.py
# Check firewall rules: sudo ufw status
```

### Issue: "Redis connection refused"
```bash
# Check Redis is running
sudo systemctl status redis-server

# Check connection
redis-cli ping
```

### Issue: "Invalid agent token (401)"
```bash
# Verify token exists in database
python manage.py shell
from apps.certificates.agent_auth import CertificateAgent
CertificateAgent.objects.filter(is_active=True).values_list('token', flat=True)
```

### Issue: "Nginx 502 Bad Gateway"
```bash
# Check Django/Gunicorn is running
sudo systemctl status certeye-django

# Check logs
tail -f /var/log/certeye/error.log
sudo tail -f /var/log/nginx/error.log
```

---

## Security Checklist

- [ ] Django DEBUG = False
- [ ] ALLOWED_HOSTS configured
- [ ] SECRET_KEY changed
- [ ] SSL/TLS certificate installed
- [ ] Database password secured
- [ ] Redis authentication enabled (optional)
- [ ] Firewall rules configured
- [ ] Backups automated
- [ ] Monitoring enabled
- [ ] Agent tokens stored securely

---

## Performance Optimization

```python
# settings.py optimizations
DATABASE_CONN_MAX_AGE = 600
SESSION_COOKIE_AGE = 86400

# Gunicorn worker count = 2 * CPU cores + 1
# For 4 cores: --workers 9
```

---

## Support & Documentation

- API Documentation: See `API_DOCUMENTATION_INTERNAL_CERTS.md`
- Architecture: See `CERTIFICATE_SERVICE_ARCHITECTURE.md`
- Troubleshooting: See `AUTH_401_TROUBLESHOOTING.md`

---

**Deployment Complete! 🎉**

Your internal certificate collection system is now running in production.

Next: Monitor submissions and adjust PowerShell agent schedule as needed.
