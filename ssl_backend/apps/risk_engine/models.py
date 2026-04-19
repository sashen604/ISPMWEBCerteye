from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class RiskRule(models.Model):
    name = models.CharField(max_length=255)
    threshold_days = models.PositiveIntegerField()
    severity = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)


class RiskConfiguration(models.Model):
    """
    Stores configurable risk scoring thresholds.
    
    Only superadmins can modify these via API.
    Changes are logged for audit trail.
    """
    
    # Expiry thresholds
    critical_expiry_days = models.PositiveIntegerField(
        default=7,
        help_text="Days until expiry to mark as CRITICAL (default: 7)"
    )
    high_expiry_days = models.PositiveIntegerField(
        default=30,
        help_text="Days until expiry to mark as HIGH (default: 30)"
    )
    medium_expiry_days = models.PositiveIntegerField(
        default=90,
        help_text="Days until expiry to mark as MEDIUM (default: 90)"
    )
    
    # Key strength thresholds
    weak_key_bits = models.PositiveIntegerField(
        default=2048,
        help_text="Key length below this is weak (default: 2048)"
    )
    medium_key_bits = models.PositiveIntegerField(
        default=3072,
        help_text="Key length below this is moderate (default: 3072)"
    )
    
    # Penalty values
    self_signed_penalty = models.PositiveIntegerField(
        default=25,
        help_text="Points to add for self-signed certificates (default: 25)"
    )
    weak_algorithm_penalty = models.PositiveIntegerField(
        default=20,
        help_text="Points to add for weak algorithms like MD5/SHA1 (default: 20)"
    )
    
    # Risk level thresholds
    critical_threshold = models.PositiveIntegerField(
        default=75,
        help_text="Risk score threshold for CRITICAL level (default: 75)"
    )
    high_threshold = models.PositiveIntegerField(
        default=50,
        help_text="Risk score threshold for HIGH level (default: 50)"
    )
    medium_threshold = models.PositiveIntegerField(
        default=25,
        help_text="Risk score threshold for MEDIUM level (default: 25)"
    )
    
    # Metadata
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Last superadmin who modified these settings"
    )
    last_modified_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last modification"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of creation"
    )
    
    class Meta:
        verbose_name = "Risk Configuration"
        verbose_name_plural = "Risk Configurations"
    
    def __str__(self):
        return f"Risk Configuration (modified: {self.last_modified_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_current_config(cls):
        """Get the current (most recent) risk configuration."""
        return cls.objects.latest('last_modified_at')
    
    def to_dict(self):
        """Convert configuration to dictionary for API responses."""
        return {
            'critical_expiry_days': self.critical_expiry_days,
            'high_expiry_days': self.high_expiry_days,
            'medium_expiry_days': self.medium_expiry_days,
            'weak_key_bits': self.weak_key_bits,
            'medium_key_bits': self.medium_key_bits,
            'self_signed_penalty': self.self_signed_penalty,
            'weak_algorithm_penalty': self.weak_algorithm_penalty,
            'critical_threshold': self.critical_threshold,
            'high_threshold': self.high_threshold,
            'medium_threshold': self.medium_threshold,
            'last_modified_by': self.last_modified_by.username if self.last_modified_by else None,
            'last_modified_at': self.last_modified_at.isoformat(),
        }

