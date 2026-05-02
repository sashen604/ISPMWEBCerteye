from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.alerts.models import Alert
from apps.alerts.services import AlertEngine
from apps.alerts.tasks import generate_expiry_alerts_task
from apps.certificates.models import Certificate

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="alerts@example.com",
    ALERT_RECIPIENTS=["security@example.com"],
)
class AlertEngineTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="alert_admin",
            email="admin@example.com",
            password="pass12345",
            role="admin",
        )
        now = timezone.now()
        self.cert = Certificate.objects.create(
            domain="alert-test.example.com",
            certificate_type="single",
            issuer="Test CA",
            subject="CN=alert-test.example.com",
            serial_number="alert-serial-1",
            signature_algorithm="sha256WithRSAEncryption",
            key_length=2048,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=7),
            days_remaining=7,
            risk_level="LOW",
            risk_score=20,
            risk_reasoning={},
            status="active",
            source_type="scanner",
        )

    def test_expiry_alert_deduped_within_window(self):
        engine = AlertEngine()
        first = engine.generate_expiry_alerts()
        second = engine.generate_expiry_alerts()
        self.assertGreaterEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        self.assertEqual(Alert.objects.count(), len(first))

    def test_immediate_high_risk_alert(self):
        self.cert.risk_level = "HIGH"
        self.cert.risk_score = 70
        self.cert.save(update_fields=["risk_level", "risk_score", "updated_at"])
        engine = AlertEngine()
        created = engine.trigger_risk_alert(self.cert)
        self.assertIsNotNone(created)
        self.assertEqual(Alert.objects.filter(certificate_id=self.cert.id, trigger_source="immediate").count(), 1)

    def test_email_sent_on_alert_creation(self):
        engine = AlertEngine()
        engine.generate_expiry_alerts()
        self.assertGreaterEqual(len(mail.outbox), 1)

    def test_periodic_task_generates_alerts(self):
        result = generate_expiry_alerts_task()
        self.assertIn("generated", result)
        self.assertIn("type", result)
