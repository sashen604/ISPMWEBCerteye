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
