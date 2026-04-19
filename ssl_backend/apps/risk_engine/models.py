from django.db import models


class RiskRule(models.Model):
    name = models.CharField(max_length=255)
    threshold_days = models.PositiveIntegerField()
    severity = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
