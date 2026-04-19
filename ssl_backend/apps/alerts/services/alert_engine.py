"""
Alert Engine Service

Provides automated alert generation and email notification system for:
- Certificate expiration warnings (CRITICAL at 7d, HIGH at 30d, MEDIUM at 90d)
- Cryptographic weakness detection (weak algorithms, weak keys, self-signed)
- Email routing to admin users
- Database persistence of alerts
- Configurable thresholds

Author: CertEye System
Date: April 19, 2026
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
    """
    Service for generating and sending alerts based on certificate conditions.
    
    Alert Types:
    - EXPIRY: Certificates expiring soon (configurable thresholds)
    - CRYPTO_WEAKNESS: Weak algorithms, weak keys, self-signed certs
    
    Severity Levels:
    - CRITICAL: Immediate action required (expires in < 7 days, broken crypto)
    - HIGH: Action required soon (expires in 7-30 days, weak key length)
    - MEDIUM: Plan for action (expires in 30-90 days)
    - LOW: Informational (expires in > 90 days)
    """

    # Default expiration thresholds (in days)
    EXPIRY_THRESHOLDS = {
        'CRITICAL': 7,
        'HIGH': 30,
        'MEDIUM': 90,
    }

    # Weak algorithms that trigger alerts
    WEAK_ALGORITHMS = [
        'sha1WithRSAEncryption',
        'md5WithRSAEncryption',
        'sha1',
        'md5',
    ]

    # Minimum key length for certificates
    WEAK_KEY_LENGTH = 2048
    STRONG_KEY_LENGTH = 3072

    def __init__(self, expiry_thresholds: Optional[Dict[str, int]] = None):
        """
        Initialize the alert engine.
        
        Args:
            expiry_thresholds: Custom thresholds for expiry alerts
                              (CRITICAL, HIGH, MEDIUM in days)
        """
        self.expiry_thresholds = expiry_thresholds or self.EXPIRY_THRESHOLDS

    def generate_expiry_alerts(self) -> List[Dict]:
        """
        Generate alerts for certificates expiring soon.
        
        Returns:
            List of alert dictionaries created
        """
        alerts_created = []
        now = timezone.now()

        # CRITICAL: Expiring within threshold
        critical_expiry = now + timedelta(days=self.expiry_thresholds['CRITICAL'])
        critical_certs = Certificate.objects.filter(
            valid_to__gte=now,
            valid_to__lte=critical_expiry,
            status='active'
        )

        for cert in critical_certs:
            days_left = (cert.valid_to - now).days
            alert = self._create_alert(
                title=f"CRITICAL: {cert.domain} expires in {days_left} days",
                severity='CRITICAL',
                message=f"Certificate for {cert.domain} (Issuer: {cert.issuer}) expires in {days_left} days on {cert.valid_to.strftime('%Y-%m-%d')}. Immediate renewal required.",
                alert_type='EXPIRY',
                certificate=cert
            )
            if alert:
                alerts_created.append(alert)

        # HIGH: Expiring within 30 days but beyond critical threshold
        high_expiry = now + timedelta(days=self.expiry_thresholds['HIGH'])
        high_certs = Certificate.objects.filter(
            valid_to__gt=critical_expiry,
            valid_to__lte=high_expiry,
            status='active'
        )

        for cert in high_certs:
            days_left = (cert.valid_to - now).days
            alert = self._create_alert(
                title=f"HIGH: {cert.domain} expires in {days_left} days",
                severity='HIGH',
                message=f"Certificate for {cert.domain} (Issuer: {cert.issuer}) expires in {days_left} days on {cert.valid_to.strftime('%Y-%m-%d')}. Renewal recommended.",
                alert_type='EXPIRY',
                certificate=cert
            )
            if alert:
                alerts_created.append(alert)

        # MEDIUM: Expiring within 90 days but beyond high threshold
        medium_expiry = now + timedelta(days=self.expiry_thresholds['MEDIUM'])
        medium_certs = Certificate.objects.filter(
            valid_to__gt=high_expiry,
            valid_to__lte=medium_expiry,
            status='active'
        )

        for cert in medium_certs:
            days_left = (cert.valid_to - now).days
            alert = self._create_alert(
                title=f"MEDIUM: {cert.domain} expires in {days_left} days",
                severity='MEDIUM',
                message=f"Certificate for {cert.domain} (Issuer: {cert.issuer}) expires in {days_left} days on {cert.valid_to.strftime('%Y-%m-%d')}. Plan for renewal.",
                alert_type='EXPIRY',
                certificate=cert
            )
            if alert:
                alerts_created.append(alert)

        logger.info(f"Generated {len(alerts_created)} expiry alerts")
        return alerts_created

    def generate_crypto_weakness_alerts(self) -> List[Dict]:
        """
        Generate alerts for cryptographic weaknesses.
        
        Detects:
        - Weak signature algorithms (SHA-1, MD5)
        - Weak key lengths (< 2048 bits)
        - Self-signed certificates
        
        Returns:
            List of alert dictionaries created
        """
        alerts_created = []

        # Check for weak algorithms (CRITICAL)
        for algorithm_variant in self.WEAK_ALGORITHMS:
            weak_algo_certs = Certificate.objects.filter(
                signature_algorithm__icontains=algorithm_variant,
                status='active'
            )

            for cert in weak_algo_certs:
                alert = self._create_alert(
                    title=f"CRITICAL: {cert.domain} uses weak algorithm {cert.signature_algorithm}",
                    severity='CRITICAL',
                    message=f"Certificate for {cert.domain} uses deprecated algorithm {cert.signature_algorithm}. "
                           f"This algorithm is vulnerable and poses a security risk. "
                           f"Immediate replacement required.",
                    alert_type='CRYPTO_WEAKNESS',
                    certificate=cert
                )
                if alert:
                    alerts_created.append(alert)

        # Check for weak key lengths (HIGH)
        weak_key_certs = Certificate.objects.filter(
            key_length__lt=self.WEAK_KEY_LENGTH,
            status='active'
        )

        for cert in weak_key_certs:
            alert = self._create_alert(
                title=f"HIGH: {cert.domain} uses {cert.key_length}-bit key (minimum recommended: 2048)",
                severity='HIGH',
                message=f"Certificate for {cert.domain} has a weak key length of {cert.key_length} bits. "
                       f"Recommended minimum is 2048 bits. Certificate replacement recommended.",
                alert_type='CRYPTO_WEAKNESS',
                certificate=cert
            )
            if alert:
                alerts_created.append(alert)

        # Check for self-signed certs (MEDIUM)
        if hasattr(Certificate, 'is_self_signed'):
            self_signed_certs = Certificate.objects.filter(
                is_self_signed=True,
                status='active'
            )

            for cert in self_signed_certs:
                alert = self._create_alert(
                    title=f"MEDIUM: {cert.domain} is self-signed",
                    severity='MEDIUM',
                    message=f"Certificate for {cert.domain} is self-signed and not issued by a trusted CA. "
                           f"This may cause browser warnings and trust issues. Consider obtaining a CA-signed certificate.",
                    alert_type='CRYPTO_WEAKNESS',
                    certificate=cert
                )
                if alert:
                    alerts_created.append(alert)

        logger.info(f"Generated {len(alerts_created)} cryptographic weakness alerts")
        return alerts_created

    def _create_alert(
        self,
        title: str,
        severity: str,
        message: str,
        alert_type: str,
        certificate: Optional[Certificate] = None
    ) -> Optional[Dict]:
        """
        Create an alert in the database and send email notification.
        
        Args:
            title: Alert title
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            message: Alert message
            alert_type: Type of alert (EXPIRY, CRYPTO_WEAKNESS)
            certificate: Associated Certificate object (optional)
            
        Returns:
            Dictionary with alert data or None if creation failed
        """
        try:
            # Check if similar alert already exists (avoid duplicates)
            # Look for same title created in last 24 hours
            existing_alert = Alert.objects.filter(
                title=title,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()

            if existing_alert:
                logger.debug(f"Alert already exists: {title}")
                return None

            # Create alert in database
            with transaction.atomic():
                alert = Alert.objects.create(
                    title=title,
                    severity=severity,
                    message=message,
                    alert_type=alert_type,
                    certificate_id=certificate.id if certificate else None,
                    certificate_domain=certificate.domain if certificate else None,
                )

                # Send email notification
                self._send_email_notification(
                    title=title,
                    severity=severity,
                    message=message,
                    alert_type=alert_type,
                    certificate=certificate
                )

            logger.info(f"Created alert: {title} (severity: {severity})")

            return {
                'id': alert.id,
                'title': alert.title,
                'severity': alert.severity,
                'message': alert.message,
                'alert_type': alert.alert_type,
                'certificate_id': alert.certificate_id,
                'certificate_domain': alert.certificate_domain,
                'created_at': alert.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            return None

    def _send_email_notification(
        self,
        title: str,
        severity: str,
        message: str,
        alert_type: str,
        certificate: Optional[Certificate] = None
    ) -> bool:
        """
        Send email notification to admin users.
        
        Args:
            title: Alert title
            severity: Severity level
            message: Alert message
            alert_type: Type of alert
            certificate: Associated Certificate object (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Get admin users
            admin_users = User.objects.filter(
                role__in=['superadmin', 'admin']
            )

            if not admin_users.exists():
                logger.warning("No admin users found for alert notification")
                return False

            admin_emails = [user.email for user in admin_users if user.email]

            if not admin_emails:
                logger.warning("No admin email addresses found")
                return False

            # Build email content
            email_subject = f"[{severity}] CertEye Alert: {title}"

            email_body = f"""
CertEye Alert Notification
{'=' * 60}

Alert Title: {title}
Severity: {severity}
Alert Type: {alert_type}
Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

"""

            if certificate:
                email_body += f"""
Certificate Details:
- Domain: {certificate.domain}
- Issuer: {certificate.issuer}
- Subject: {certificate.subject}
- Expires: {certificate.valid_to.strftime('%Y-%m-%d %H:%M:%S')}
- Days Remaining: {certificate.days_remaining}
- Risk Level: {certificate.risk_level}
- Risk Score: {certificate.risk_score}/100

"""

            email_body += f"""
Action Required:
Please log in to the CertEye dashboard to review this alert and take appropriate action.

Dashboard: {self._get_dashboard_url()}
Alert Severity Guide:
- CRITICAL: Immediate action required
- HIGH: Action required within 1-7 days
- MEDIUM: Plan for action within 1-3 months
- LOW: Informational only

---
This is an automated alert from CertEye Certificate Monitoring System.
Please do not reply to this email.
"""

            # Send email
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )

            logger.info(f"Email notification sent to {len(admin_emails)} admins for alert: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False

    def _get_dashboard_url(self) -> str:
        """Get the dashboard URL (from settings or default)."""
        return getattr(settings, 'DASHBOARD_URL', 'http://localhost:5173/dashboard')
