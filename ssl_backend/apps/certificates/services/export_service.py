"""
Certificate Export Service

Provides comprehensive CSV export functionality for certificates with multiple
filtering scenarios including: all certificates, expiring certificates, high-risk
certificates, by issuer, critical alerts, and custom filters.

Author: CertEye System
Date: April 19, 2026
"""

import csv
import io
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models import Q, QuerySet

from apps.certificates.models import Certificate


class CertificateExportService:
    """
    Service for exporting certificates to CSV with multiple filtering options.
    
    Features:
    - Export all certificates
    - Export expiring certificates (within N days threshold)
    - Export high-risk certificates (risk score >= threshold)
    - Export certificates by issuer
    - Export critical alerts (expiring within 7 days + CRITICAL risk)
    - Export with custom filters
    - Configurable CSV headers and columns
    """

    # Standard CSV headers for certificate export
    STANDARD_HEADERS = [
        'Domain',
        'Subject',
        'Issuer',
        'Certificate Type',
        'Valid From',
        'Expires',
        'Days Remaining',
        'Key Length',
        'Signature Algorithm',
        'Serial Number',
        'Thumbprint',
        'Risk Level',
        'Risk Score',
        'Status',
        'Source Type',
        'Last Scanned',
        'Created At'
    ]

    def __init__(self, exclude_fields: Optional[List[str]] = None):
        """
        Initialize the export service.
        
        Args:
            exclude_fields: List of field names to exclude from export
        """
        self.exclude_fields = exclude_fields or []
        self.headers = [h for h in self.STANDARD_HEADERS if h not in self.exclude_fields]

    def export_all_certificates(self) -> tuple[str, bytes]:
        """
        Export all certificates to CSV.
        
        Returns:
            Tuple of (filename, csv_content)
        """
        queryset = Certificate.objects.all().order_by('-created_at')
        filename = f"certificates_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def export_expiring_certificates(self, days_threshold: int = 30) -> tuple[str, bytes]:
        """
        Export certificates expiring within N days.
        
        Args:
            days_threshold: Number of days to look ahead (default 30)
            
        Returns:
            Tuple of (filename, csv_content)
        """
        if days_threshold < 0:
            raise ValueError("days_threshold must be non-negative")

        now = timezone.now()
        expiry_date = now + timedelta(days=days_threshold)

        queryset = Certificate.objects.filter(
            valid_to__gte=now,
            valid_to__lte=expiry_date,
            status='active'
        ).order_by('valid_to')

        filename = f"certificates_expiring_{days_threshold}d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def export_high_risk_certificates(self, risk_threshold: int = 60) -> tuple[str, bytes]:
        """
        Export certificates with risk score >= threshold.
        
        Args:
            risk_threshold: Minimum risk score to include (0-100)
            
        Returns:
            Tuple of (filename, csv_content)
        """
        if not (0 <= risk_threshold <= 100):
            raise ValueError("risk_threshold must be between 0 and 100")

        queryset = Certificate.objects.filter(
            risk_score__gte=risk_threshold,
            status='active'
        ).order_by('-risk_score')

        filename = f"certificates_high_risk_{risk_threshold}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def export_by_issuer(self, issuer: str) -> tuple[str, bytes]:
        """
        Export certificates from a specific issuer.
        
        Args:
            issuer: Issuer name to filter by
            
        Returns:
            Tuple of (filename, csv_content)
        """
        queryset = Certificate.objects.filter(
            issuer__icontains=issuer,
            status='active'
        ).order_by('domain')

        filename = f"certificates_issuer_{issuer.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def export_critical_alerts(self) -> tuple[str, bytes]:
        """
        Export critical alerts: certificates expiring within 7 days OR with CRITICAL risk level.
        
        Returns:
            Tuple of (filename, csv_content)
        """
        now = timezone.now()
        critical_expiry = now + timedelta(days=7)

        queryset = Certificate.objects.filter(
            Q(
                valid_to__gte=now,
                valid_to__lte=critical_expiry,
                status='active'
            ) |
            Q(risk_level__iexact='CRITICAL', status='active')
        ).distinct().order_by('valid_to')

        filename = f"certificates_critical_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def export_custom_filter(self, filters: Dict[str, Any]) -> tuple[str, bytes]:
        """
        Export certificates with custom filters.
        
        Supported filters:
        - domain_contains: str - Filter domains containing this string
        - issuer: str - Filter by issuer name
        - risk_level: str - Filter by risk level (CRITICAL, HIGH, MEDIUM, LOW)
        - risk_score_min: int - Minimum risk score
        - risk_score_max: int - Maximum risk score
        - key_length_min: int - Minimum key length
        - key_length_max: int - Maximum key length
        - valid_from_start: datetime - Filter certs valid from this date or later
        - valid_to_start: datetime - Filter certs expiring from this date or later
        - valid_to_end: datetime - Filter certs expiring before this date
        - status: str - Filter by status (active, revoked, etc.)
        - source_type: str - Filter by source (scanner, internal, adcs)
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Tuple of (filename, csv_content)
        """
        queryset = Certificate.objects.all()

        # Domain filter
        if domain_contains := filters.get('domain_contains'):
            queryset = queryset.filter(domain__icontains=domain_contains)

        # Issuer filter
        if issuer := filters.get('issuer'):
            queryset = queryset.filter(issuer__icontains=issuer)

        # Risk level filter
        if risk_level := filters.get('risk_level'):
            queryset = queryset.filter(risk_level__iexact=risk_level)

        # Risk score range
        if risk_score_min := filters.get('risk_score_min'):
            queryset = queryset.filter(risk_score__gte=risk_score_min)
        if risk_score_max := filters.get('risk_score_max'):
            queryset = queryset.filter(risk_score__lte=risk_score_max)

        # Key length range
        if key_length_min := filters.get('key_length_min'):
            queryset = queryset.filter(key_length__gte=key_length_min)
        if key_length_max := filters.get('key_length_max'):
            queryset = queryset.filter(key_length__lte=key_length_max)

        # Validity dates
        if valid_from_start := filters.get('valid_from_start'):
            queryset = queryset.filter(valid_from__gte=valid_from_start)
        if valid_to_start := filters.get('valid_to_start'):
            queryset = queryset.filter(valid_to__gte=valid_to_start)
        if valid_to_end := filters.get('valid_to_end'):
            queryset = queryset.filter(valid_to__lte=valid_to_end)

        # Status filter
        if status := filters.get('status'):
            queryset = queryset.filter(status__iexact=status)

        # Source type filter
        if source_type := filters.get('source_type'):
            queryset = queryset.filter(source_type__iexact=source_type)

        queryset = queryset.order_by('-created_at')

        filename = f"certificates_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        content = self._generate_csv(queryset)
        return filename, content

    def _generate_csv(self, queryset: QuerySet) -> bytes:
        """
        Generate CSV content from a queryset of certificates.
        
        Args:
            queryset: QuerySet of Certificate objects
            
        Returns:
            CSV content as bytes
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(self.headers)

        # Write certificate rows
        for cert in queryset:
            row = self._certificate_to_row(cert)
            writer.writerow(row)

        # Convert to bytes
        csv_content = output.getvalue()
        return csv_content.encode('utf-8')

    def _certificate_to_row(self, cert: Certificate) -> List[str]:
        """
        Convert a certificate object to a CSV row.
        
        Args:
            cert: Certificate model instance
            
        Returns:
            List of values for the CSV row
        """
        row_data = {
            'Domain': cert.domain,
            'Subject': cert.subject,
            'Issuer': cert.issuer,
            'Certificate Type': cert.certificate_type,
            'Valid From': cert.valid_from.strftime('%Y-%m-%d %H:%M:%S'),
            'Expires': cert.valid_to.strftime('%Y-%m-%d %H:%M:%S'),
            'Days Remaining': str(cert.days_remaining),
            'Key Length': str(cert.key_length),
            'Signature Algorithm': cert.signature_algorithm,
            'Serial Number': cert.serial_number,
            'Thumbprint': cert.thumbprint or 'N/A',
            'Risk Level': cert.risk_level,
            'Risk Score': str(cert.risk_score),
            'Status': cert.status,
            'Source Type': cert.source_type,
            'Last Scanned': cert.last_scanned.strftime('%Y-%m-%d %H:%M:%S') if cert.last_scanned else 'Never',
            'Created At': cert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Apply exclude_fields
        return [row_data[header] for header in self.headers if header in row_data]
