from rest_framework import serializers
from .models import RiskRule, RiskConfiguration


class RiskRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRule
        fields = '__all__'


class RiskConfigurationSerializer(serializers.ModelSerializer):
    last_modified_by = serializers.CharField(
        source='last_modified_by.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = RiskConfiguration
        fields = [
            'id',
            'critical_expiry_days',
            'high_expiry_days',
            'medium_expiry_days',
            'weak_key_bits',
            'medium_key_bits',
            'self_signed_penalty',
            'weak_algorithm_penalty',
            'critical_threshold',
            'high_threshold',
            'medium_threshold',
            'last_modified_by',
            'last_modified_at',
            'created_at',
        ]
        read_only_fields = ['id', 'last_modified_by', 'last_modified_at', 'created_at']

