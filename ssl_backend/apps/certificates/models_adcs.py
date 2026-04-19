"""
AD CS (Active Directory Certificate Services) Models
Stores registration info, sync history, and imported AD CS certificates.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ADCSSource(models.Model):
    """
    Represents a registered Active Directory Certificate Services source.
    Stores connection information for fetching internal PKI certificates.
    """
    
    SOURCE_TYPE_CHOICES = [
        ('winrm', 'WinRM PowerShell'),
        ('ldap', 'LDAP Query'),
        ('agent', 'Local Agent'),
    ]
    
    # Basic identification
    source_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Friendly name for this AD CS source"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this AD CS server"
    )
    
    # Server connection details
    server_hostname = models.CharField(
        max_length=255,
        help_text="FQDN or IP address of AD CS server"
    )
    server_ip = models.CharField(
        max_length=45,
        help_text="IPv4 or IPv6 address of AD CS server"
    )
    ca_name = models.CharField(
        max_length=255,
        help_text="Common Name of the Certificate Authority"
    )
    domain = models.CharField(
        max_length=255,
        help_text="NETBIOS domain or DNS domain"
    )
    
    # Authentication
    username = models.CharField(max_length=255)
    encrypted_password = models.TextField(
        help_text="Encrypted service account password"
    )
    
    # Connection configuration
    auth_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default='winrm'
    )
    port = models.PositiveIntegerField(
        default=5985,
        help_text="WinRM port (5985=HTTP, 5986=HTTPS)"
    )
    use_ssl = models.BooleanField(
        default=True,
        help_text="Use HTTPS for WinRM connection"
    )
    verify_ssl = models.BooleanField(
        default=True,
        help_text="Verify SSL certificate"
    )
    
    # Status tracking
    connection_status = models.CharField(
        max_length=50,
        choices=[
            ('connected', 'Connected'),
            ('disconnected', 'Disconnected'),
            ('error', 'Connection Error'),
            ('untested', 'Not Tested'),
        ],
        default='untested'
    )
    last_connection_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful connection time"
    )
    connection_error = models.TextField(
        blank=True,
        help_text="Last connection error message"
    )
    
    # Sync configuration
    auto_sync_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic daily sync"
    )
    sync_interval_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours between automatic syncs"
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync time"
    )
    certificate_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of certificates currently stored from this source"
    )
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Active sources appear in dashboard"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='adcs_sources_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'ca_name']),
            models.Index(fields=['connection_status']),
            models.Index(fields=['last_sync_at']),
        ]
    
    def __str__(self):
        return f"{self.source_name} ({self.ca_name})"


class ADCSCredentialHistory(models.Model):
    """
    Audit trail for credential changes on AD CS sources.
    Tracks when credentials were updated and by whom.
    """
    
    source = models.ForeignKey(
        ADCSSource,
        on_delete=models.CASCADE,
        related_name='credential_history'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    change_type = models.CharField(
        max_length=50,
        choices=[
            ('password_updated', 'Password Updated'),
            ('username_updated', 'Username Updated'),
            ('auth_type_changed', 'Auth Type Changed'),
        ]
    )
    password_hash = models.CharField(
        max_length=255,
        help_text="SHA256 hash of old password for audit"
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['source', '-changed_at']),
        ]


class ADCSSyncHistory(models.Model):
    """
    Track all sync operations for an AD CS source.
    Useful for monitoring, troubleshooting, and audit purposes.
    """
    
    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('failed', 'Failed'),
    ]
    
    source = models.ForeignKey(
        ADCSSource,
        on_delete=models.CASCADE,
        related_name='sync_history'
    )
    sync_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('scheduled', 'Scheduled'),
            ('on_demand', 'On-Demand'),
        ],
        default='manual'
    )
    status = models.CharField(
        max_length=50,
        choices=SYNC_STATUS_CHOICES,
        default='pending'
    )
    
    # Sync statistics
    certificates_fetched = models.PositiveIntegerField(default=0)
    certificates_imported = models.PositiveIntegerField(default=0)
    certificates_updated = models.PositiveIntegerField(default=0)
    certificates_failed = models.PositiveIntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    sync_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed sync information"
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total sync duration in seconds"
    )
    
    # User tracking
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source', '-started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.source.source_name} - {self.get_status_display()} ({self.started_at})"


class ADCSConnectionTest(models.Model):
    """
    Records connection test results for troubleshooting.
    """
    
    TEST_STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]
    
    source = models.ForeignKey(
        ADCSSource,
        on_delete=models.CASCADE,
        related_name='connection_tests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    test_results = models.JSONField(
        help_text="Detailed test results"
    )
    overall_status = models.CharField(
        max_length=50,
        choices=TEST_STATUS_CHOICES
    )
    message = models.TextField()
    tested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.source.source_name} - {self.get_overall_status_display()} ({self.created_at})"


class ADCSCertificate(models.Model):
    """
    Extended certificate information specific to AD CS sources.
    Links AD CS-specific metadata to the main Certificate model.
    """
    
    certificate = models.OneToOneField(
        'Certificate',
        on_delete=models.CASCADE,
        related_name='adcs_metadata'
    )
    source = models.ForeignKey(
        ADCSSource,
        on_delete=models.CASCADE
    )
    
    # AD CS specific fields
    request_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="AD CS request ID"
    )
    template_name = models.CharField(
        max_length=255,
        help_text="Certificate template used"
    )
    requester = models.CharField(
        max_length=255,
        blank=True,
        help_text="User or machine that requested cert"
    )
    approver = models.CharField(
        max_length=255,
        blank=True,
        help_text="User who approved the request"
    )
    status_code = models.PositiveIntegerField(
        default=0,
        help_text="AD CS status code"
    )
    dns_names = models.JSONField(
        default=list,
        help_text="List of DNS names/SANs"
    )
    
    # Lifecycle tracking
    issued_at = models.DateTimeField(
        help_text="When certificate was issued"
    )
    renewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When certificate was last renewed"
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When certificate was revoked (if applicable)"
    )
    
    # Audit
    imported_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['source', 'template_name']),
            models.Index(fields=['request_id']),
        ]
    
    def __str__(self):
        return f"{self.certificate.domain} - {self.template_name} (ID: {self.request_id})"
