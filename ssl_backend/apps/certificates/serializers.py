from rest_framework import serializers
from .models import Certificate, Domain, DomainScanHistory


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            'id', 'domain', 'hostname', 'certificate_type', 'issuer', 'subject',
            'serial_number', 'signature_algorithm', 'key_length', 'valid_from',
            'valid_to', 'days_remaining', 'risk_level', 'risk_score', 'last_scanned',
            'source_type', 'status', 'thumbprint', 'template_name', 'agent_id',
            'source_priority', 'certificate_chain', 'last_verified', 'is_self_signed',
            'san_list', 'crypto_findings', 'risk_reasoning', 'created_at', 'updated_at',
            'acknowledged_at',
        ]
        read_only_fields = [
            'id',
            'days_remaining',
            'risk_level',
            'risk_score',
            'created_at',
            'updated_at',
        ]


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = [
            "id",
            "name",
            "is_enabled",
            "last_scan_at",
            "last_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_scan_at", "last_status", "created_at", "updated_at"]


class DomainScanHistorySerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)

    class Meta:
        model = DomainScanHistory
        fields = [
            "id",
            "domain",
            "domain_name",
            "scanned_at",
            "status",
            "error_message",
            "certificate",
            "parsed_data",
            "risk_score",
            "risk_level",
            "risk_reasoning",
            "created_at",
        ]
        read_only_fields = fields


class InternalCertificatePayloadSerializer(serializers.Serializer):
    """
    Validates PowerShell agent certificate payload.
    
    Accepts both single certificate and batch formats.
    """
    
    # Required fields
    hostname = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Hostname/server name (optional, uses server_name if missing)"
    )
    server_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Alternative field for hostname (from PowerShell)"
    )
    subject = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Certificate subject"
    )
    issuer = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Certificate issuer"
    )
    thumbprint = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Certificate thumbprint (unique identifier)"
    )
    valid_from = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Certificate validity start date"
    )
    valid_to = serializers.DateTimeField(
        required=True,
        help_text="Certificate validity end date"
    )
    expiry_date = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Alternative field for valid_to (from PowerShell)"
    )
    
    # Optional fields
    certificate_template = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Windows certificate template name"
    )
    template_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Alternative field for certificate_template"
    )
    signature_algorithm = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        default='Unknown',
        help_text="Certificate signature algorithm"
    )
    key_length = serializers.IntegerField(
        required=False,
        default=2048,
        help_text="RSA key length in bits"
    )
    
    def validate(self, data):
        """Validate and normalize incoming data."""
        # Use hostname or server_name
        hostname = data.get('hostname') or data.get('server_name')
        if not hostname:
            raise serializers.ValidationError("Either 'hostname' or 'server_name' is required")
        data['hostname'] = hostname
        
        # Use valid_to or expiry_date
        valid_to = data.get('valid_to') or data.get('expiry_date')
        if not valid_to:
            raise serializers.ValidationError("Either 'valid_to' or 'expiry_date' is required")
        data['valid_to'] = valid_to
        
        # Use certificate_template or template_name
        template = data.get('certificate_template') or data.get('template_name')
        if template:
            data['certificate_template'] = template
        
        # Ensure thumbprint is uppercase
        if data.get('thumbprint'):
            data['thumbprint'] = data['thumbprint'].upper()
        
        # Set default valid_from if not provided
        if not data.get('valid_from'):
            data['valid_from'] = data.get('valid_to')
        
        return data


class InternalCertificateBatchSerializer(serializers.Serializer):
    """Validates batch of PowerShell agent certificates."""
    
    certificates = serializers.ListField(
        child=InternalCertificatePayloadSerializer(),
        required=True,
        allow_empty=False,
        help_text="Array of certificate objects"
    )
    update_if_exists = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Update existing certificates if found"
    )


class InternalCertificateIngestionResponseSerializer(serializers.Serializer):
    """Response format for certificate ingestion."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    status = serializers.CharField()  # 'created', 'updated', or 'error'
    certificate = CertificateSerializer(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)


class InternalCertificateBatchResponseSerializer(serializers.Serializer):
    """Response format for batch ingestion."""
    
    total = serializers.IntegerField()
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    failed = serializers.IntegerField()
    results = serializers.ListField(
        child=serializers.JSONField()
    )
