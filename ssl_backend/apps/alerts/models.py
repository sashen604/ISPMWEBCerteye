from django.db import models
from django.utils import timezone


class Alert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('EXPIRY', 'Certificate Expiry'),
        ('CRYPTO_WEAKNESS', 'Cryptographic Weakness'),
        ('OTHER', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    title = models.CharField(max_length=255, db_index=True)
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, db_index=True)
    message = models.TextField()
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES, default='OTHER', db_index=True)
    certificate_id = models.IntegerField(null=True, blank=True, db_index=True, help_text="Associated Certificate ID")
    certificate_domain = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Associated Certificate Domain")
    is_acknowledged = models.BooleanField(default=False, help_text="Whether alert has been acknowledged by admin")
    acknowledged_by = models.CharField(max_length=255, null=True, blank=True, help_text="Username who acknowledged the alert")
    acknowledged_at = models.DateTimeField(null=True, blank=True, help_text="When alert was acknowledged")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['alert_type', 'certificate_domain']),
        ]
    
    def __str__(self):
        return f"[{self.severity}] {self.title}"
