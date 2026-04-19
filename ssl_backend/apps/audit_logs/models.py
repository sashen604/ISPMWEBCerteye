from django.db import models


class AuditLog(models.Model):
    actor = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
