from django.db import models
from django.utils import timezone


class Certificate(models.Model):
    domain = models.CharField(max_length=255, db_index=True)
    certificate_type = models.CharField(max_length=100)
    issuer = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=128, db_index=True)
    signature_algorithm = models.CharField(max_length=128)
    key_length = models.PositiveIntegerField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(db_index=True)
    days_remaining = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=50)
    risk_score = models.PositiveIntegerField(default=0)
    last_scanned = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=50, default='agent')
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['valid_to']

    def __str__(self):
        return f"{self.domain}:{self.serial_number}"
