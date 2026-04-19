from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
import json


class User(AbstractUser):
    # Role definitions
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    ROLE_VIEWER = 'viewer'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, 'Super Admin'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
        (ROLE_VIEWER, 'Viewer'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=ROLE_USER)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    # Security settings
    enable_2fa = models.BooleanField(default=False, help_text="Require 2FA for all logins")
    login_notifications = models.BooleanField(default=True, help_text="Get alerts when someone logs in")
    suspicious_login_alerts = models.BooleanField(default=True, help_text="Alert on logins from new locations")
    ip_whitelist_enabled = models.BooleanField(default=False, help_text="Only allow logins from approved IPs")
    
    # Policy settings
    session_timeout_minutes = models.IntegerField(default=30, help_text="Auto-logout after inactivity (minutes)")
    password_expiry_days = models.IntegerField(default=90, help_text="Require password change (days)")
    api_key_rotation_days = models.IntegerField(default=90, help_text="Rotate API keys (days)")
    last_password_change = models.DateTimeField(null=True, blank=True)
    
    # User preferences
    dark_mode = models.BooleanField(default=False, help_text="Enable dark theme")
    
    # Security tracking
    two_fa_secret = models.CharField(max_length=32, blank=True, null=True)
    two_fa_backup_codes = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_superadmin(self):
        return self.role == self.ROLE_SUPERADMIN
    
    def is_admin(self):
        return self.role in [self.ROLE_SUPERADMIN, self.ROLE_ADMIN]
    
    def can_manage_users(self):
        return self.is_superadmin()


class UserLoginLog(models.Model):
    """Track user login/logout activities"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_successful = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    session_duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")

    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['-login_time']),
        ]

    def __str__(self):
        status = 'SUCCESS' if self.is_successful else 'FAILED'
        return f"{self.user.username} - {self.login_time} ({status})"


class UserRegistrationLog(models.Model):
    """Track user registrations and account changes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registration_logs')
    registration_time = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    initial_role = models.CharField(max_length=50, default='user')
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='users_registered')

    class Meta:
        ordering = ['-registration_time']
        indexes = [
            models.Index(fields=['-registration_time']),
        ]

    def __str__(self):
        return f"{self.user.username} - Registered at {self.registration_time}"


class UserAuditLog(models.Model):
    """Track administrative changes to users"""
    ACTION_CHOICES = [
        ('role_change', 'Role Changed'),
        ('password_reset', 'Password Reset'),
        ('user_created', 'User Created'),
        ('user_deleted', 'User Deleted'),
        ('user_deactivated', 'User Deactivated'),
        ('user_activated', 'User Activated'),
        ('email_changed', 'Email Changed'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_actions_performed')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_actions_received')
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['target_user', '-timestamp']),
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.actor.username if self.actor else 'System'} - {self.get_action_display()} on {self.target_user.username}"


class UserSession(models.Model):
    """Track active user sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.browser} ({self.ip_address})"
    
    @property
    def is_expired(self):
        """Check if session has expired based on user's timeout setting"""
        timeout_minutes = self.user.session_timeout_minutes
        time_since_activity = (timezone.now() - self.last_activity).total_seconds() / 60
        return time_since_activity > timeout_minutes


class IPWhitelist(models.Model):
    """Store whitelisted IP addresses for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ip_whitelist')
    ip_address = models.GenericIPAddressField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'ip_address']
        ordering = ['-last_used']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"


class APIKey(models.Model):
    """Manage API keys for programmatic access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=128, unique=True)
    secret = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    scopes = models.JSONField(default=list, blank=True)  # List of API scopes
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def is_expired(self):
        """Check if API key is expired"""
        if not self.is_active:
            return True
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    @staticmethod
    def generate_key():
        """Generate a unique API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_secret():
        """Generate a unique API secret"""
        return secrets.token_urlsafe(32)


class SecurityAuditLog(models.Model):
    """Log all security-related events"""
    EVENT_TYPES = [
        ('login_success', 'Successful Login'),
        ('login_failed', 'Failed Login'),
        ('login_suspicious', 'Suspicious Login'),
        ('password_changed', 'Password Changed'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('api_key_created', 'API Key Created'),
        ('api_key_revoked', 'API Key Revoked'),
        ('session_terminated', 'Session Terminated'),
        ('ip_whitelisted', 'IP Whitelisted'),
        ('settings_changed', 'Settings Changed'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_audit_logs')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='success', choices=[
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('warning', 'Warning'),
    ])
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} ({self.timestamp})"


class SuspiciousLoginAttempt(models.Model):
    """Track and manage suspicious login attempts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspicious_attempts')
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    reason = models.TextField()  # Why this login is considered suspicious
    is_verified = models.BooleanField(default=False)  # User confirmed this was them
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Suspicious attempt from {self.ip_address}"