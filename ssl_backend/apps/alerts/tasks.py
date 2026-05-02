from celery import shared_task

from apps.alerts.services import AlertEngine


@shared_task
def generate_expiry_alerts_task():
    engine = AlertEngine()
    alerts = engine.generate_expiry_alerts()
    return {"generated": len(alerts), "type": "expiry"}


@shared_task
def generate_risk_alerts_task():
    engine = AlertEngine()
    alerts = engine.generate_immediate_risk_alerts()
    return {"generated": len(alerts), "type": "risk"}
