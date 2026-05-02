from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id',
            'title',
            'severity',
            'message',
            'alert_type',
            'dedupe_key',
            'threshold_days',
            'trigger_source',
            'certificate_id',
            'certificate_domain',
            'is_acknowledged',
            'acknowledged_by',
            'acknowledged_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
