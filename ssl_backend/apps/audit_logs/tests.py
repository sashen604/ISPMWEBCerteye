from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit_logs.models import AuditLog

User = get_user_model()


class AuditLogRBACSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="audit_admin",
            email="audit_admin@test.com",
            password="pass12345",
            role=User.ROLE_ADMIN,
        )
        self.viewer = User.objects.create_user(
            username="audit_viewer",
            email="audit_viewer@test.com",
            password="pass12345",
            role=User.ROLE_VIEWER,
        )
        AuditLog.objects.create(
            user=self.admin,
            action="other",
            target_type="security",
            target_id="1",
            details={"message": "seed"},
        )

    def test_viewer_is_denied_audit_log_endpoint(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_audit_log_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))
