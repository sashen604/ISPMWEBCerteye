"""
Test file for new certificate services (Export and Alert Engine)

This file demonstrates usage of the new services and can be run with:
python manage.py test apps.certificates.tests --verbosity=2
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json
from rest_framework.test import APIClient

from apps.certificates.models import Certificate
from apps.certificates.services import CertificateExportService
from apps.certificates.models import Domain, DomainScanHistory
from apps.certificates.tasks import scan_all_enabled_domains_task
from apps.alerts.models import Alert
from apps.alerts.services import AlertEngine
from apps.risk_engine.services import RiskScoringEngine
from unittest.mock import patch

User = get_user_model()


class CertificateExportServiceTestCase(TestCase):
    """Tests for CertificateExportService."""
    
    def setUp(self):
        """Create test certificates."""
        now = timezone.now()
        
        # Create expiring certificate (CRITICAL)
        self.cert_critical_expiry = Certificate.objects.create(
            domain='expiring-critical.example.com',
            certificate_type='X.509',
            issuer='Let\'s Encrypt',
            subject='expiring-critical.example.com',
            serial_number='critical_001',
            signature_algorithm='sha256WithRSAEncryption',
            key_length=2048,
            valid_from=now - timedelta(days=365),
            valid_to=now + timedelta(days=5),  # Expires in 5 days
            days_remaining=5,
            risk_level='CRITICAL',
            risk_score=95,
            status='active',
            thumbprint='abc123critical'
        )
        
        # Create high-risk certificate
        self.cert_high_risk = Certificate.objects.create(
            domain='high-risk.example.com',
            certificate_type='X.509',
            issuer='Self-Signed',
            subject='high-risk.example.com',
            serial_number='high_risk_001',
            signature_algorithm='sha1WithRSAEncryption',
            key_length=1024,
            valid_from=now - timedelta(days=180),
            valid_to=now + timedelta(days=100),
            days_remaining=100,
            risk_level='HIGH',
            risk_score=75,
            status='active',
            thumbprint='abc123high'
        )
        
        # Create low-risk certificate
        self.cert_low_risk = Certificate.objects.create(
            domain='low-risk.example.com',
            certificate_type='X.509',
            issuer='DigiCert',
            subject='low-risk.example.com',
            serial_number='low_risk_001',
            signature_algorithm='sha256WithRSAEncryption',
            key_length=4096,
            valid_from=now - timedelta(days=180),
            valid_to=now + timedelta(days=700),
            days_remaining=700,
            risk_level='LOW',
            risk_score=5,
            status='active',
            thumbprint='abc123low'
        )
    
    def test_export_all_certificates(self):
        """Test exporting all certificates."""
        service = CertificateExportService()
        filename, content = service.export_all_certificates()
        
        self.assertIn('certificates_all_', filename)
        self.assertIn('.csv', filename)
        self.assertIn(b'expiring-critical.example.com', content)
        self.assertIn(b'high-risk.example.com', content)
        self.assertIn(b'low-risk.example.com', content)
    
    def test_export_expiring_certificates(self):
        """Test exporting expiring certificates."""
        service = CertificateExportService()
        filename, content = service.export_expiring_certificates(days_threshold=30)
        
        self.assertIn(b'expiring-critical.example.com', content)
        # Other certs shouldn't be included (they expire beyond 30 days)
    
    def test_export_high_risk_certificates(self):
        """Test exporting high-risk certificates."""
        service = CertificateExportService()
        filename, content = service.export_high_risk_certificates(risk_threshold=60)
        
        self.assertIn(b'high-risk.example.com', content)
        self.assertIn(b'expiring-critical.example.com', content)
        # Low-risk shouldn't be included
    
    def test_export_critical_alerts(self):
        """Test exporting critical alerts."""
        service = CertificateExportService()
        filename, content = service.export_critical_alerts()
        
        # Should include CRITICAL risk or expiring < 7 days
        self.assertIn(b'expiring-critical.example.com', content)
    
    def test_export_by_issuer(self):
        """Test exporting by issuer."""
        service = CertificateExportService()
        filename, content = service.export_by_issuer('DigiCert')
        
        self.assertIn(b'low-risk.example.com', content)
        self.assertNotIn(b'high-risk.example.com', content)
    
    def test_export_custom_filter(self):
        """Test exporting with custom filters."""
        service = CertificateExportService()
        
        filters = {
            'domain_contains': 'example',
            'risk_level': 'HIGH',
        }
        filename, content = service.export_custom_filter(filters)
        
        self.assertIn(b'high-risk.example.com', content)


class AlertEngineTestCase(TestCase):
    """Tests for AlertEngine."""
    
    def setUp(self):
        """Create test data."""
        now = timezone.now()
        
        # Create expiring certificate
        self.cert_expiring = Certificate.objects.create(
            domain='expiring.test.com',
            certificate_type='X.509',
            issuer='Let\'s Encrypt',
            subject='expiring.test.com',
            serial_number='exp_001',
            signature_algorithm='sha256WithRSAEncryption',
            key_length=2048,
            valid_from=now - timedelta(days=365),
            valid_to=now + timedelta(days=5),
            days_remaining=5,
            risk_level='CRITICAL',
            risk_score=90,
            status='active',
            thumbprint='expiring_thumb'
        )
        
        # Create weak crypto certificate
        self.cert_weak_crypto = Certificate.objects.create(
            domain='weak-crypto.test.com',
            certificate_type='X.509',
            issuer='Old CA',
            subject='weak-crypto.test.com',
            serial_number='weak_001',
            signature_algorithm='sha1WithRSAEncryption',
            key_length=1024,
            valid_from=now - timedelta(days=365),
            valid_to=now + timedelta(days=365),
            days_remaining=365,
            risk_level='HIGH',
            risk_score=75,
            status='active',
            thumbprint='weak_thumb'
        )
        
        # Create test user (admin)
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='superadmin'
        )
    
    def test_alert_engine_initialization(self):
        """Test AlertEngine initialization with custom thresholds."""
        custom_thresholds = {'CRITICAL': 10, 'HIGH': 60, 'MEDIUM': 120}
        engine = AlertEngine(expiry_thresholds=custom_thresholds)
        
        self.assertEqual(engine.expiry_thresholds, custom_thresholds)
    
    def test_generate_expiry_alerts(self):
        """Test generating expiry alerts."""
        engine = AlertEngine()
        alerts = engine.generate_expiry_alerts()
        
        # Should have created at least one alert for expiring cert
        self.assertGreater(len(alerts), 0)
    
    def test_generate_crypto_weakness_alerts(self):
        """Test generating crypto weakness alerts."""
        engine = AlertEngine()
        alerts = engine.generate_crypto_weakness_alerts()
        
        # Should have created alert for weak algorithm
        self.assertGreater(len(alerts), 0)


class CertificateExportAPITestCase(TestCase):
    """Tests for Certificate Export API endpoints."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_export',
            email='test_export@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test certificate
        now = timezone.now()
        self.certificate = Certificate.objects.create(
            domain='api-test.example.com',
            certificate_type='X.509',
            issuer='Test CA',
            subject='api-test.example.com',
            serial_number='api_001',
            signature_algorithm='sha256WithRSAEncryption',
            key_length=2048,
            valid_from=now - timedelta(days=180),
            valid_to=now + timedelta(days=180),
            days_remaining=180,
            risk_level='LOW',
            risk_score=10,
            status='active',
            thumbprint='api_thumb'
        )
    
    def test_export_csv_all_endpoint(self):
        """Test CSV export endpoint with 'all' filter."""
        # Make request
        response = self.client.get('/api/certificates/export_csv/?filter_type=all')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(b'api-test.example.com', response.content)
    
    def test_export_csv_expiring_endpoint(self):
        """Test CSV export endpoint with 'expiring' filter."""
        response = self.client.get('/api/certificates/export_csv/?filter_type=expiring&days_threshold=30')
        
        # Certificate expires in 180 days, so shouldn't be included
        self.assertEqual(response.status_code, 200)


class AlertAPITestCase(TestCase):
    """Tests for Alert API endpoints."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@test.com',
            password='adminpass123',
            role='superadmin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test alert
        self.alert = Alert.objects.create(
            title='Test Alert',
            severity='HIGH',
            message='This is a test alert',
            alert_type='EXPIRY',
            certificate_domain='test.example.com'
        )
    
    def test_get_alerts_endpoint(self):
        """Test getting alerts."""
        response = self.client.get('/api/alerts/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)
    
    def test_alert_statistics_endpoint(self):
        """Test getting alert statistics."""
        response = self.client.get('/api/alerts/stats/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('statistics', data)


class WeightedRiskScoringTestCase(TestCase):
    def test_risk_classification_boundaries(self):
        self.assertEqual(RiskScoringEngine.determine_risk_level(25), "LOW")
        self.assertEqual(RiskScoringEngine.determine_risk_level(26), "MEDIUM")
        self.assertEqual(RiskScoringEngine.determine_risk_level(50), "MEDIUM")
        self.assertEqual(RiskScoringEngine.determine_risk_level(51), "HIGH")
        self.assertEqual(RiskScoringEngine.determine_risk_level(75), "HIGH")
        self.assertEqual(RiskScoringEngine.determine_risk_level(76), "CRITICAL")

    def test_weighted_reasons_payload(self):
        result = RiskScoringEngine.calculate_weighted_risk(
            days_remaining=5,
            valid_to=timezone.now() + timedelta(days=5),
            key_length=1024,
            is_self_signed=True,
            algorithm="sha1WithRSAEncryption",
            crypto_findings={"issues": ["weak key"], "is_weak_key": True, "is_weak_algorithm": True},
        )
        self.assertIn("components", result)
        self.assertIn("weighted_formula", result)
        self.assertIn("risk_reasons", result)
        self.assertGreaterEqual(result["total_score"], 0)
        self.assertLessEqual(result["total_score"], 100)


class DomainManagementAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="domainadmin",
            email="domainadmin@test.com",
            password="testpass123",
            role="admin",
        )
        self.client.force_authenticate(user=self.user)

    def test_domain_crud_and_toggle(self):
        create_res = self.client.post(
            "/api/certificates/domains/",
            data=json.dumps({"name": "example.org", "is_enabled": True}),
            content_type="application/json",
        )
        self.assertEqual(create_res.status_code, 201)
        domain_id = create_res.json()["id"]

        disable_res = self.client.post(f"/api/certificates/domains/{domain_id}/disable/")
        self.assertEqual(disable_res.status_code, 200)
        enable_res = self.client.post(f"/api/certificates/domains/{domain_id}/enable/")
        self.assertEqual(enable_res.status_code, 200)

        delete_res = self.client.delete(f"/api/certificates/domains/{domain_id}/")
        self.assertEqual(delete_res.status_code, 204)


class DomainScanHistoryAndTasksTestCase(TestCase):
    def setUp(self):
        self.domain_enabled = Domain.objects.create(name="enabled.example.com", is_enabled=True)
        self.domain_disabled = Domain.objects.create(name="disabled.example.com", is_enabled=False)

    @patch("apps.certificates.tasks.scan_domain_task.delay")
    def test_periodic_scheduler_queues_only_enabled_domains(self, delay_mock):
        result = scan_all_enabled_domains_task()
        self.assertEqual(result["scheduled_count"], 1)
        delay_mock.assert_called_once_with(self.domain_enabled.id)

    def test_history_model_persists_snapshots(self):
        history = DomainScanHistory.objects.create(
            domain=self.domain_enabled,
            status=DomainScanHistory.STATUS_SUCCESS,
            parsed_data={"subject": "CN=enabled.example.com"},
            risk_score=44,
            risk_level="MEDIUM",
            risk_reasoning={"risk_reasons": ["test"]},
        )
        self.assertEqual(history.domain, self.domain_enabled)
        self.assertEqual(history.risk_level, "MEDIUM")
