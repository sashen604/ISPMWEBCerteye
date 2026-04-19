from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserLoginLog, UserRegistrationLog, UserAuditLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_superadmin = serializers.BooleanField(source='is_superadmin', read_only=True)
    is_admin = serializers.BooleanField(source='is_admin', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display', 'is_superadmin', 'is_admin', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


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
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLoginLog
        fields = ['id', 'username', 'login_time', 'logout_time', 'ip_address', 'is_successful', 'failure_reason', 'session_duration']
        read_only_fields = ['id', 'login_time', 'logout_time', 'session_duration']


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
