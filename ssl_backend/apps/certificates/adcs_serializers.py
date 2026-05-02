"""
AD CS Serializers - REST API serializers for AD CS operations.
"""

from rest_framework import serializers
from .models_adcs import ADCSSource, ADCSSyncHistory, ADCSConnectionTest, ADCSCredentialHistory


class ADCSSourceSerializer(serializers.ModelSerializer):
    """Serializer for AD CS source registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Password (required for create, optional for update)"
    )
    connection_status_display = serializers.CharField(
        source='get_connection_status_display',
        read_only=True
    )
    auth_type_display = serializers.CharField(
        source='get_auth_type_display',
        read_only=True
    )
    
    class Meta:
        model = ADCSSource
        fields = [
            'id',
            'source_name',
            'description',
            'server_hostname',
            'server_ip',
            'ca_name',
            'domain',
            'username',
            'password',  # Write-only field
            'auth_type',
            'auth_type_display',
            'port',
            'use_ssl',
            'verify_ssl',
            'connection_status',
            'connection_status_display',
            'last_connection_at',
            'auto_sync_enabled',
            'sync_interval_hours',
            'certificate_count',
            'last_sync_at',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'connection_status',
            'connection_status_display',
            'last_connection_at',
            'certificate_count',
            'last_sync_at',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        """
        Keep WinRM transport settings consistent:
        - 5985 => HTTP (use_ssl=False)
        - 5986 => HTTPS (use_ssl=True)
        Coerce port to int (JSON / HTML number inputs often send strings).
        """
        raw_port = attrs.get('port', getattr(self.instance, 'port', 5985))
        try:
            port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {'port': 'Must be a valid port number.'}
            ) from exc
        attrs['port'] = port
        if port == 5985:
            attrs['use_ssl'] = False
        elif port == 5986:
            attrs['use_ssl'] = True
        return attrs
    
    def create(self, validated_data):
        """Create new AD CS source with encrypted password."""
        from .adcs_crypto import ADCSCredentialEncryption
        
        password = validated_data.pop('password', '')
        
        if not password:
            raise serializers.ValidationError("Password is required when creating AD CS source")

        try:
            validated_data['encrypted_password'] = ADCSCredentialEncryption.encrypt(password)
        except ValueError as exc:
            raise serializers.ValidationError(
                {"password": [str(exc)]}
            ) from exc

        source = super().create(validated_data)

        request = self.context.get("request")
        ADCSCredentialHistory.objects.create(
            source=source,
            changed_by=getattr(request, "user", None),
            change_type='password_updated',
            password_hash=ADCSCredentialEncryption.hash_password(password),
            ip_address=(request.META.get('REMOTE_ADDR', '') if request else ''),
        )
        return source
    
    def update(self, instance, validated_data):
        """Update AD CS source with encrypted password if provided."""
        from .adcs_crypto import ADCSCredentialEncryption
        
        password = validated_data.pop('password', '')
        username_changed = 'username' in validated_data and validated_data.get('username') != instance.username
        auth_type_changed = 'auth_type' in validated_data and validated_data.get('auth_type') != instance.auth_type
        
        if password:
            try:
                validated_data['encrypted_password'] = ADCSCredentialEncryption.encrypt(password)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"password": [str(exc)]}
                ) from exc

        source = super().update(instance, validated_data)

        request = self.context.get("request")
        changed_by = getattr(request, "user", None)
        ip_address = request.META.get('REMOTE_ADDR', '') if request else ''
        if password:
            ADCSCredentialHistory.objects.create(
                source=source,
                changed_by=changed_by,
                change_type='password_updated',
                password_hash=ADCSCredentialEncryption.hash_password(password),
                ip_address=ip_address,
            )
        if username_changed:
            ADCSCredentialHistory.objects.create(
                source=source,
                changed_by=changed_by,
                change_type='username_updated',
                password_hash='',
                ip_address=ip_address,
            )
        if auth_type_changed:
            ADCSCredentialHistory.objects.create(
                source=source,
                changed_by=changed_by,
                change_type='auth_type_changed',
                password_hash='',
                ip_address=ip_address,
            )
        return source


class ADCSConnectionTestSerializer(serializers.ModelSerializer):
    """Serializer for connection test results."""
    
    status_display = serializers.CharField(
        source='get_overall_status_display',
        read_only=True
    )
    
    class Meta:
        model = ADCSConnectionTest
        fields = [
            'id',
            'source',
            'test_results',
            'overall_status',
            'status_display',
            'message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ADCSSyncHistorySerializer(serializers.ModelSerializer):
    """Serializer for sync history and results."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    source_name = serializers.CharField(
        source='source.source_name',
        read_only=True
    )
    
    class Meta:
        model = ADCSSyncHistory
        fields = [
            'id',
            'source',
            'source_name',
            'status',
            'status_display',
            'certificates_fetched',
            'certificates_imported',
            'certificates_updated',
            'certificates_failed',
            'duration_seconds',
            'sync_details',
            'error_message',
            'completed_at',
            'started_at'
        ]
        read_only_fields = [
            'id',
            'certificates_fetched',
            'certificates_imported',
            'certificates_updated',
            'certificates_failed',
            'duration_seconds',
            'sync_details',
            'error_message',
            'completed_at',
            'started_at'
        ]
