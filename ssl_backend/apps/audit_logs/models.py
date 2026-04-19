from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AuditLog(models.Model):
    """Generic audit log for general actions."""
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('certificate_create', 'Certificate Created'),
        ('certificate_update', 'Certificate Updated'),
        ('certificate_delete', 'Certificate Deleted'),
        ('certificate_scan', 'Certificate Scan'),
        ('alert_create', 'Alert Created'),
        ('alert_update', 'Alert Updated'),
        ('alert_resolve', 'Alert Resolved'),
        ('role_change', 'Role Changed'),
        ('risk_config_update', 'Risk Configuration Updated'),
        ('agent_submission', 'Agent Submission'),
        ('internal_cert_submission', 'Internal Certificate Submission'),
        ('other', 'Other Action'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=100, blank=True)  # e.g., 'certificate', 'alert'
    target_id = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)  # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"{self.action} - {self.user} - {self.created_at}"


class CertificateAuditLog(models.Model):
    """Audit log for certificate operations."""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('scan', 'Scanned'),
        ('import', 'Imported'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    certificate_id = models.IntegerField(null=True, blank=True)  # May be null if cert was deleted
    certificate_name = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    old_values = models.JSONField(default=dict, blank=True)  # Previous state (for updates/deletes)
    new_values = models.JSONField(default=dict, blank=True)  # New state (for creates/updates)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['certificate_id']),
        ]

    def __str__(self):
        return f"{self.action} - {self.certificate_name} - {self.user} - {self.timestamp}"


class AlertAuditLog(models.Model):
    """Audit log for alert operations."""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('resolve', 'Resolved'),
        ('reopen', 'Reopened'),
        ('dismiss', 'Dismissed'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    alert_id = models.IntegerField(null=True, blank=True)  # May be null if alert was deleted
    alert_type = models.CharField(max_length=100, blank=True)
    certificate_id = models.IntegerField(null=True, blank=True)
    certificate_name = models.CharField(max_length=255, blank=True)
    old_values = models.JSONField(default=dict, blank=True)  # Previous state
    new_values = models.JSONField(default=dict, blank=True)  # New state
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['alert_id']),
            models.Index(fields=['certificate_id']),
        ]

    def __str__(self):
        return f"{self.action} - Alert #{self.alert_id} - {self.user} - {self.timestamp}"
