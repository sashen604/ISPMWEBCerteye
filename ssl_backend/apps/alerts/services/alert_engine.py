"""Alert engine for expiry/risk notifications with dedupe and SMTP delivery."""

import logging
from typing import Dict, List, Optional
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.certificates.models import Certificate
from apps.alerts.models import Alert

User = get_user_model()
logger = logging.getLogger(__name__)


class AlertEngine:
    EXPIRY_THRESHOLDS = [90, 30, 14, 7]
    DEDUPE_WINDOW_HOURS = 6

    def __init__(self, expiry_thresholds: Optional[List[int]] = None):
        self.expiry_thresholds = sorted(expiry_thresholds or self.EXPIRY_THRESHOLDS, reverse=True)

    def generate_expiry_alerts(self) -> List[Dict]:
        alerts_created = []
        now = timezone.now()

        for threshold in self.expiry_thresholds:
            certs = Certificate.objects.filter(
                status='active',
                valid_to__gte=now,
                valid_to__lte=now + timedelta(days=threshold),
            )
            for cert in certs:
                days_left = max(0, (cert.valid_to - now).days)
                if days_left > threshold:
                    continue
                severity = self._severity_for_threshold(threshold)
                title = f"{severity}: {cert.domain} expires in {days_left} days"
                message = (
                    f"Certificate for {cert.domain} expires in {days_left} days on "
                    f"{cert.valid_to.strftime('%Y-%m-%d %H:%M:%S')}."
                )
                dedupe_key = f"expiry:{cert.id}:{severity}:{threshold}"
                alert = self._create_alert(
                    title=title,
                    severity=severity,
                    message=message,
                    alert_type='EXPIRY',
                    certificate=cert,
                    dedupe_key=dedupe_key,
                    threshold_days=threshold,
                    trigger_source='scheduled',
                )
                if alert:
                    alerts_created.append(alert)
        return alerts_created

    def trigger_risk_alert(self, certificate: Certificate, trigger_source: str = 'immediate') -> Optional[Dict]:
        """Trigger immediate alerts for HIGH/CRITICAL risk certificates."""
        if not certificate or certificate.risk_level not in {'HIGH', 'CRITICAL'}:
            return None
        severity = 'CRITICAL' if certificate.risk_level == 'CRITICAL' else 'HIGH'
        title = f"{severity}: {certificate.domain} risk level is {certificate.risk_level}"
        message = (
            f"Certificate {certificate.domain} has risk level {certificate.risk_level} "
            f"with score {certificate.risk_score}."
        )
        dedupe_key = f"risk:{certificate.id}:{certificate.risk_level}"
        return self._create_alert(
            title=title,
            severity=severity,
            message=message,
            alert_type='OTHER',
            certificate=certificate,
            dedupe_key=dedupe_key,
            threshold_days=None,
            trigger_source=trigger_source,
        )

    def generate_immediate_risk_alerts(self) -> List[Dict]:
        """Generate immediate-style alerts for all currently high/critical certificates."""
        alerts = []
        candidates = Certificate.objects.filter(status='active', risk_level__in=['HIGH', 'CRITICAL'])
        for cert in candidates:
            created = self.trigger_risk_alert(cert, trigger_source='scheduled')
            if created:
                alerts.append(created)
        return alerts

    def _create_alert(
        self,
        *,
        title: str,
        severity: str,
        message: str,
        alert_type: str,
        certificate: Optional[Certificate],
        dedupe_key: str,
        threshold_days: Optional[int],
        trigger_source: str,
    ) -> Optional[Dict]:
        try:
            existing_alert = Alert.objects.filter(
                dedupe_key=dedupe_key,
                created_at__gte=timezone.now() - timedelta(hours=self.DEDUPE_WINDOW_HOURS),
            ).exists()
            if existing_alert:
                return None

            with transaction.atomic():
                alert = Alert.objects.create(
                    title=title,
                    severity=severity,
                    message=message,
                    alert_type=alert_type,
                    dedupe_key=dedupe_key,
                    threshold_days=threshold_days,
                    trigger_source=trigger_source,
                    certificate_id=certificate.id if certificate else None,
                    certificate_domain=certificate.domain if certificate else None,
                )
                self._send_email_notification(alert=alert, certificate=certificate)

            return {
                'id': alert.id,
                'title': alert.title,
                'severity': alert.severity,
                'message': alert.message,
                'alert_type': alert.alert_type,
                'dedupe_key': alert.dedupe_key,
                'threshold_days': alert.threshold_days,
                'trigger_source': alert.trigger_source,
                'certificate_id': alert.certificate_id,
                'certificate_domain': alert.certificate_domain,
                'created_at': alert.created_at.isoformat(),
            }
        except Exception as exc:
            logger.error(f"Failed to create alert: {exc}")
            return None

    def _send_email_notification(self, *, alert: Alert, certificate: Optional[Certificate]) -> bool:
        try:
            recipients = self._resolve_recipients()
            if not recipients:
                return False

            email_subject = f"[{alert.severity}] CertEye Alert: {alert.title}"
            email_body = (
                "CertEye Alert Notification\n"
                "============================================================\n\n"
                f"Alert Title: {alert.title}\n"
                f"Severity: {alert.severity}\n"
                f"Alert Type: {alert.alert_type}\n"
                f"Triggered By: {alert.trigger_source}\n"
                f"Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Message:\n{alert.message}\n\n"
            )
            if certificate:
                email_body += (
                    "Certificate Details:\n"
                    f"- Domain: {certificate.domain}\n"
                    f"- Issuer: {certificate.issuer}\n"
                    f"- Expires: {certificate.valid_to.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"- Risk Level: {certificate.risk_level}\n"
                    f"- Risk Score: {certificate.risk_score}/100\n\n"
                )
            email_body += (
                f"Dashboard: {self._get_dashboard_url()}\n\n"
                "This is an automated alert from CertEye.\n"
            )

            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
            return True
        except Exception as exc:
            logger.error(f"Failed to send email notification: {exc}")
            return False

    def _resolve_recipients(self) -> List[str]:
        admin_users = User.objects.filter(role__in=['superadmin', 'admin'])
        role_emails = [u.email for u in admin_users if u.email]
        configured = list(getattr(settings, "ALERT_RECIPIENTS", []))
        return sorted(set([email for email in role_emails + configured if email]))

    @staticmethod
    def _severity_for_threshold(threshold: int) -> str:
        if threshold <= 7:
            return 'CRITICAL'
        if threshold <= 30:
            return 'HIGH'
        return 'MEDIUM'

    def _get_dashboard_url(self) -> str:
        return getattr(settings, 'DASHBOARD_URL', 'http://localhost:5173/dashboard')
