from django.db import models


class Alert(models.Model):
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
