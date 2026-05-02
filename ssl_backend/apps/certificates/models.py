from django.db import models
from django.utils import timezone


class Certificate(models.Model):
    domain = models.CharField(max_length=255, db_index=True)
    hostname = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    certificate_type = models.CharField(max_length=100)
    issuer = models.CharField(max_length=255, db_index=True)
    subject = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=128, db_index=True)
    signature_algorithm = models.CharField(max_length=128)
    key_length = models.PositiveIntegerField(db_index=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(db_index=True)
    days_remaining = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=50, db_index=True)
    risk_score = models.PositiveIntegerField(default=0)
    risk_reasoning = models.JSONField(default=dict, blank=True, help_text="Detailed breakdown of risk calculation (for audit trail)")
    last_scanned = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=50, default='scanner', db_index=True)
    status = models.CharField(max_length=50, default='active', db_index=True)
    thumbprint = models.CharField(max_length=255, null=True, blank=True, unique=True, db_index=True)
    template_name = models.CharField(max_length=255, null=True, blank=True)
    agent_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    source_priority = models.IntegerField(default=0, help_text="Priority for deduplication: 100=internal, 50=scanner")
    certificate_chain = models.JSONField(default=list, blank=True, help_text="List of intermediate/root cert data")
    last_verified = models.DateTimeField(null=True, blank=True, help_text="Last validation timestamp")
    is_self_signed = models.BooleanField(default=False, db_index=True, help_text="Whether certificate is self-signed")
    san_list = models.JSONField(default=list, blank=True, help_text="List of Subject Alternative Names")
    crypto_findings = models.JSONField(default=dict, blank=True, help_text="Detailed cryptographic analysis (algorithm strength, key analysis)")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Operator acknowledged review (internal / workflow)",
    )

    class Meta:
        ordering = ['valid_to']
        indexes = [
            models.Index(fields=['domain', 'source_type']),
            models.Index(fields=['valid_to', 'status']),
            models.Index(fields=['risk_level', 'source_type']),
        ]

    def __str__(self):
        return f"{self.domain}:{self.serial_number}"


class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    is_enabled = models.BooleanField(default=True, db_index=True)
    last_scan_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DomainScanHistory(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="scan_history",
    )
    scanned_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    error_message = models.TextField(blank=True, null=True)

    certificate = models.ForeignKey(
        Certificate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="domain_scan_history",
    )
    parsed_data = models.JSONField(default=dict, blank=True)
    risk_score = models.PositiveIntegerField(default=0)
    risk_level = models.CharField(max_length=50, blank=True, default="")
    risk_reasoning = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-scanned_at"]
        indexes = [
            models.Index(fields=["domain", "-scanned_at"]),
            models.Index(fields=["status", "-scanned_at"]),
        ]

    def __str__(self):
        return f"{self.domain.name} @ {self.scanned_at} [{self.status}]"
