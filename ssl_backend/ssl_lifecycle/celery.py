import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssl_lifecycle.settings")

app = Celery("ssl_lifecycle")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "scan-enabled-domains-every-24-hours": {
        "task": "apps.certificates.tasks.scan_all_enabled_domains_task",
        "schedule": crontab(minute=0, hour=0),
    },
    "generate-expiry-alerts-every-hour": {
        "task": "apps.alerts.tasks.generate_expiry_alerts_task",
        "schedule": crontab(minute=0),
    },
    "generate-risk-alerts-every-15-minutes": {
        "task": "apps.alerts.tasks.generate_risk_alerts_task",
        "schedule": crontab(minute="*/15"),
    },
}
