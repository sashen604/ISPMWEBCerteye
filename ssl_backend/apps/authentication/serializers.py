from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserLoginLog, UserRegistrationLog, UserAuditLog,
    UserSession, IPWhitelist, APIKey, SecurityAuditLog, SuspiciousLoginAttempt
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_superadmin = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display', 'is_superadmin', 'is_admin', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_is_superadmin(self, obj):
        return obj.is_superadmin()
    
    def get_is_admin(self, obj):
        return obj.is_admin()


class UserListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role', 'is_active']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=User.ROLE_USER  # New users default to USER role
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserLoginLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLoginLog
        fields = ['id', 'username', 'attempted_username', 'login_time', 'logout_time', 'ip_address', 'is_successful', 'failure_reason', 'session_duration']
        read_only_fields = ['id', 'login_time', 'logout_time', 'session_duration']

    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        return obj.attempted_username


class UserRegistrationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    registered_by_username = serializers.CharField(source='registered_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = UserRegistrationLog
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'initial_role', 'registration_time', 'registered_by_username']
        read_only_fields = ['id', 'registration_time']


class UserAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, allow_null=True)
    target_username = serializers.CharField(source='target_user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = UserAuditLog
        fields = ['id', 'action', 'action_display', 'actor_username', 'target_username', 'old_value', 'new_value', 'timestamp', 'ip_address']
        read_only_fields = ['id', 'timestamp']


class UserSecuritySettingsSerializer(serializers.ModelSerializer):
    """Serializer for user security settings"""
    class Meta:
        model = User
        fields = [
            'enable_2fa',
            'login_notifications',
            'suspicious_login_alerts',
            'ip_whitelist_enabled',
            'session_timeout_minutes',
            'password_expiry_days',
            'api_key_rotation_days',
            'dark_mode',
        ]


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for active user sessions"""
    class Meta:
        model = UserSession
        fields = ['id', 'ip_address', 'browser', 'device', 'created_at', 'last_activity', 'is_active']
        read_only_fields = ['id', 'created_at', 'last_activity']


class IPWhitelistSerializer(serializers.ModelSerializer):
    """Serializer for IP whitelist management"""
    class Meta:
        model = IPWhitelist
        fields = ['id', 'ip_address', 'description', 'created_at', 'last_used']
        read_only_fields = ['id', 'created_at', 'last_used']


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API key management"""
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'created_at', 'last_used', 'is_active', 'expires_at']
        read_only_fields = ['id', 'created_at', 'last_used']


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for creating API keys (includes secret)"""
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'secret', 'created_at', 'last_used', 'is_active', 'expires_at', 'scopes']
        read_only_fields = ['id', 'key', 'secret', 'created_at', 'last_used']


class SecurityAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for security audit logs"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = SecurityAuditLog
        fields = ['id', 'event_type', 'event_type_display', 'description', 'ip_address', 'browser', 'device', 'status', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']


class SuspiciousLoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for suspicious login attempts"""
    class Meta:
        model = SuspiciousLoginAttempt
        fields = ['id', 'ip_address', 'location', 'browser', 'device', 'reason', 'is_verified', 'timestamp']
        read_only_fields = ['id', 'timestamp']
