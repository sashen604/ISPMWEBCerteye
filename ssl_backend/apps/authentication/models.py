from django.contrib.auth.models import AbstractUser
from django.db import models


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
