from rest_framework import serializers
from .models import AuditLog, CertificateAuditLog, AlertAuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_username', 'action', 'action_display', 'target_type', 
                  'target_id', 'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']


class CertificateAuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = CertificateAuditLog
        fields = ['id', 'user', 'user_username', 'action', 'action_display', 'certificate_id',
                  'certificate_name', 'domain', 'old_values', 'new_values', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class AlertAuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AlertAuditLog
        fields = ['id', 'user', 'user_username', 'action', 'action_display', 'alert_id',
                  'alert_type', 'certificate_id', 'certificate_name', 'old_values', 'new_values',
                  'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']
