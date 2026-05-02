from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.authentication.models import UserLoginLog
from apps.certificates.models import Domain

User = get_user_model()


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="sec_admin",
            email="sec_admin@test.com",
            password="pass12345",
            role=User.ROLE_ADMIN,
        )
        self.viewer = User.objects.create_user(
            username="sec_viewer",
            email="sec_viewer@test.com",
            password="pass12345",
            role=User.ROLE_VIEWER,
        )

    def test_jwt_lifetime_configuration(self):
        self.assertEqual(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(), 15 * 60)
        self.assertEqual(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(), 7 * 24 * 60 * 60)

    def test_login_failure_for_unknown_user_is_logged(self):
        response = self.client.post(
            "/api/auth/login",
            {"username": "unknown_user", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        log = UserLoginLog.objects.latest("login_time")
        self.assertFalse(log.is_successful)
        self.assertIsNone(log.user)
        self.assertEqual(log.attempted_username, "unknown_user")

    def test_login_success_is_logged(self):
        response = self.client.post(
            "/api/auth/login",
            {"username": self.admin.username, "password": "pass12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        log = UserLoginLog.objects.latest("login_time")
        self.assertTrue(log.is_successful)
        self.assertEqual(log.user_id, self.admin.id)
        self.assertEqual(log.attempted_username, self.admin.username)

    def test_viewer_cannot_trigger_scan(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post(
            "/api/certificates/scan/",
            {"domain": "example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_domain(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/certificates/domains/",
            {"name": "auth-test.example.com", "is_enabled": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Domain.objects.filter(name="auth-test.example.com").exists())
