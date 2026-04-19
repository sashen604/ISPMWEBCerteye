"""
Django Admin Configuration for Certificate Model

Provides a user-friendly interface for managing SSL/TLS certificates
in the Django admin panel.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface for Certificate model with custom displays and filters."""
    
    # Display configuration
    list_display = (
        'domain',
        'certificate_type',
        'issuer_short',
        'expiration_status',
        'risk_badge',
        'key_length_display',
        'last_scanned_display',
    )
    
    # Filtering options
    list_filter = (
        'status',
        'risk_level',
        'certificate_type',
        'signature_algorithm',
        ('valid_to', admin.RelatedOnlyFieldListFilter),
        'created_at',
        'last_scanned',
    )
    
    # Search fields
    search_fields = (
        'domain',
        'subject',
        'issuer',
        'serial_number',
    )
    
    # Ordering
    ordering = ('-valid_to',)  # Most recently expiring first
    
    # Read-only fields
    readonly_fields = (
        'serial_number',
        'created_at',
        'updated_at',
        'last_scanned',
        'days_remaining',
        'certificate_info_display',
    )
    
    # Fieldsets for organized display
    fieldsets = (
        ('Certificate Basics', {
            'fields': ('domain', 'certificate_type', 'status', 'last_scanned')
        }),
        ('Certificate Details', {
            'fields': (
                'certificate_info_display',
                'subject',
                'issuer_short',
                'serial_number',
                'signature_algorithm',
            ),
            'classes': ('collapse',)
        }),
        ('Validity & Expiration', {
            'fields': (
                'valid_from',
                'valid_to',
                'days_remaining',
            )
        }),
        ('Security Assessment', {
            'fields': (
                'key_length',
                'risk_level',
                'risk_score',
                'source_type',
            )
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 50
    
    def issuer_short(self, obj):
        """Display truncated issuer name."""
        issuer = obj.issuer or 'Unknown'
        return issuer[:50] + '...' if len(issuer) > 50 else issuer
    issuer_short.short_description = 'Issuer'
    
    def expiration_status(self, obj):
        """Display expiration status with color coding."""
        days = obj.days_remaining
        
        if days < 0:
            color = '#dc3545'  # Red
            status = 'Expired'
        elif days < 7:
            color = '#fd7e14'  # Orange
            status = f'{days} days'
        elif days < 30:
            color = '#ffc107'  # Yellow
            status = f'{days} days'
        else:
            color = '#28a745'  # Green
            status = f'{days} days'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    expiration_status.short_description = 'Expires In'
    
    def risk_badge(self, obj):
        """Display risk level with color-coded badge."""
        risk_level = obj.risk_level or 'unknown'
        
        color_map = {
            'critical': '#dc3545',  # Red
            'high': '#fd7e14',      # Orange
            'medium': '#ffc107',    # Yellow
            'low': '#28a745',       # Green
        }
        
        color = color_map.get(risk_level, '#6c757d')  # Gray as default
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{} ({}/100)</span>',
            color,
            risk_level.upper(),
            obj.risk_score
        )
    risk_badge.short_description = 'Risk'
    
    def key_length_display(self, obj):
        """Display key length with security assessment."""
        key_length = obj.key_length
        
        if key_length < 2048:
            icon = '❌'
            color = '#dc3545'  # Red - weak
        elif key_length < 3072:
            icon = '⚠️'
            color = '#ffc107'  # Yellow - acceptable
        else:
            icon = '✅'
            color = '#28a745'  # Green - strong
        
        return format_html(
            '<span style="color: {};">{} {} bits</span>',
            color,
            icon,
            key_length
        )
    key_length_display.short_description = 'Key Length'
    
    def last_scanned_display(self, obj):
        """Display last scanned timestamp."""
        if obj.last_scanned:
            return obj.last_scanned.strftime('%Y-%m-%d %H:%M:%S')
        return '—'
    last_scanned_display.short_description = 'Last Scanned'
    
    def certificate_info_display(self, obj):
        """Display comprehensive certificate information."""
        return format_html(
            '<div style="font-family: monospace; font-size: 12px; '
            'background-color: #f5f5f5; padding: 10px; border-radius: 4px;">'
            '<strong>Subject:</strong><br/>{}<br/><br/>'
            '<strong>Issuer:</strong><br/>{}<br/><br/>'
            '<strong>Serial Number:</strong><br/>{}</div>',
            obj.subject.replace('\n', '<br/>'),
            obj.issuer.replace('\n', '<br/>'),
            obj.serial_number,
        )
    certificate_info_display.short_description = 'Certificate Information'
    
    def has_delete_permission(self, request):
        """Allow deletion only for superusers."""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Disable manual certificate creation through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but restrict editing to superusers."""
        if request.user.is_superuser:
            return True
        # Allow viewing without editing
        return request.method in ('GET', 'HEAD', 'OPTIONS')
    
    actions = ['mark_as_active', 'mark_as_expired']
    
    def mark_as_active(self, request, queryset):
        """Admin action to mark certificates as active."""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} certificate(s) marked as active.')
    mark_as_active.short_description = 'Mark selected as active'
    
    def mark_as_expired(self, request, queryset):
        """Admin action to mark certificates as expired."""
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} certificate(s) marked as expired.')
    mark_as_expired.short_description = 'Mark selected as expired'
