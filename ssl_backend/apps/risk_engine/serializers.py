from rest_framework import serializers
from .models import RiskRule


class RiskRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRule
        fields = '__all__'
