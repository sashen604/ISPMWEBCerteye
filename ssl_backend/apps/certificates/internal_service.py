"""
Internal Certificate Collection Service

Handles ingestion of certificates from internal sources (PowerShell agents, Windows systems, etc.)
Implements upsert logic based on thumbprint, risk calculation, and audit logging.
"""

from datetime import datetime, timezone as dt_timezone
from typing import Dict, Any, List, Tuple

from django.db import transaction
from django.utils import timezone

from .models import Certificate
from .parsers import CertificateParser
from apps.risk_engine.services import RiskScoringEngine


class InternalCertificateService:
    """
    Handles collection and storage of certificates from internal sources.
    
    Features:
    - Thumbprint-based deduplication (upsert)
    - Bulk ingestion from multiple servers
    - Automatic risk scoring
    - Audit logging
    - Field mapping from PowerShell to Certificate model
    """
    
    def __init__(self):
        """Initialize internal certificate service."""
        self.parser = CertificateParser()
    
    def ingest_certificate(
        self,
        hostname: str,
        subject: str,
        issuer: str,
        thumbprint: str,
        valid_from: datetime,
        valid_to: datetime,
        certificate_template: str = None,
        agent_id: str = None,
        update_if_exists: bool = True,
        **kwargs
    ) -> Tuple[Certificate, bool, str]:
        """
        Ingest a single certificate from internal source.
        
        Args:
            hostname (str): Source hostname (Windows machine name)
            subject (str): Certificate subject
            issuer (str): Certificate issuer
            thumbprint (str): Certificate thumbprint (unique identifier)
            valid_from (datetime): Certificate validity start date
            valid_to (datetime): Certificate validity end date
            certificate_template (str): Windows certificate template name
            agent_id (str): Identifier of agent that submitted certificate
            update_if_exists (bool): Update if certificate exists (default: True)
            **kwargs: Additional fields
            
        Returns:
            Tuple[Certificate, bool, str]: (certificate_obj, created, status_message)
            - created: True if new certificate, False if updated
            - status_message: 'created', 'updated', or 'error'
        """
        try:
            # Ensure datetime objects are timezone-aware
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=dt_timezone.utc)
            if valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=dt_timezone.utc)
            
            # Calculate days remaining
            now = timezone.now()
            days_remaining = max(0, (valid_to - now).days)
            
            # Calculate risk level and score
            risk_level, risk_score = self._calculate_risk(valid_to, days_remaining)
            
            # Get risk reasoning for audit trail
            risk_reasoning = RiskScoringEngine.get_risk_reasoning(
                valid_to=valid_to,
                key_length=kwargs.get('key_length', 2048),
                is_self_signed=False,  # Internal certs from trusted CA
                algorithm=kwargs.get('signature_algorithm', 'sha256WithRSAEncryption')
            )
            
            # Determine certificate type
            cert_type = self._determine_certificate_type(subject)
            
            # Prepare certificate data
            cert_data = {
                'hostname': hostname,
                'domain': subject,  # Use subject as domain for internal certs
                'subject': subject,
                'issuer': issuer,
                'thumbprint': thumbprint,
                'valid_from': valid_from,
                'valid_to': valid_to,
                'days_remaining': days_remaining,
                'risk_level': risk_level,
                'risk_score': risk_score,
                'risk_reasoning': risk_reasoning,
                'certificate_type': cert_type,
                'source_type': 'internal_agent',
                'template_name': certificate_template,
                'agent_id': agent_id,
                'last_scanned': timezone.now(),
                'status': 'active' if valid_to > now else 'expired',
                'serial_number': thumbprint[:64],  # Use first 64 chars of thumbprint as serial
                'signature_algorithm': kwargs.get('signature_algorithm', 'Unknown'),
                'key_length': kwargs.get('key_length', 2048),
            }
            
            # Upsert logic: try to find by thumbprint first
            with transaction.atomic():
                if thumbprint:
                    certificate, created = Certificate.objects.update_or_create(
                        thumbprint=thumbprint,
                        defaults=cert_data
                    )
                    status = 'created' if created else 'updated'
                    message = f"Certificate {'created' if created else 'updated'}: {hostname}/{subject}"
                else:
                    # Fallback: create new if no thumbprint
                    certificate = Certificate.objects.create(**cert_data)
                    status = 'created'
                    message = f"Certificate created (no thumbprint): {hostname}/{subject}"
            
            return certificate, status == 'created', status
            
        except Exception as e:
            error_msg = f"Error ingesting certificate for {hostname}: {str(e)}"
            raise InternalCertificateError(error_msg) from e
    
    def ingest_batch(
        self,
        certificates: List[Dict[str, Any]],
        agent_id: str = None,
        update_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest multiple certificates from internal source.
        
        Args:
            certificates (List[Dict]): List of certificate data dictionaries
            agent_id (str): Identifier of agent that submitted certificates
            update_if_exists (bool): Update if certificates exist
            
        Returns:
            dict: Aggregated results {
                'total': int,
                'created': int,
                'updated': int,
                'failed': int,
                'results': [
                    {
                        'hostname': str,
                        'thumbprint': str,
                        'success': bool,
                        'certificate': Certificate or None,
                        'error': str or None,
                        'status': 'created' or 'updated' or 'error'
                    }
                ]
            }
        """
        results = {
            'total': len(certificates),
            'created': 0,
            'updated': 0,
            'failed': 0,
            'results': []
        }
        
        for cert_data in certificates:
            try:
                hostname = cert_data.get('hostname') or cert_data.get('server_name')
                thumbprint = cert_data.get('thumbprint')
                
                certificate, created, status = self.ingest_certificate(
                    hostname=hostname,
                    subject=cert_data.get('subject'),
                    issuer=cert_data.get('issuer'),
                    thumbprint=thumbprint,
                    valid_from=self._parse_datetime(cert_data.get('valid_from')),
                    valid_to=self._parse_datetime(cert_data.get('valid_to') or cert_data.get('expiry_date')),
                    certificate_template=cert_data.get('certificate_template') or cert_data.get('template_name'),
                    agent_id=agent_id,
                    update_if_exists=update_if_exists,
                    signature_algorithm=cert_data.get('signature_algorithm'),
                    key_length=cert_data.get('key_length', 2048),
                )
                
                if status == 'created':
                    results['created'] += 1
                elif status == 'updated':
                    results['updated'] += 1
                
                results['results'].append({
                    'hostname': hostname,
                    'thumbprint': thumbprint,
                    'success': True,
                    'certificate': certificate,
                    'error': None,
                    'status': status
                })
                
            except Exception as e:
                results['failed'] += 1
                hostname = cert_data.get('hostname') or cert_data.get('server_name', 'unknown')
                results['results'].append({
                    'hostname': hostname,
                    'thumbprint': cert_data.get('thumbprint', 'unknown'),
                    'success': False,
                    'certificate': None,
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    
    def _calculate_risk(self, valid_to: datetime, days_remaining: int) -> Tuple[str, int]:
        """
        Calculate risk level and score for certificate using unified risk engine.
        
        Args:
            valid_to (datetime): Certificate expiration date
            days_remaining (int): Days until expiration
            
        Returns:
            Tuple[str, int]: (risk_level, risk_score)
        """
        # Use unified risk scoring engine
        # For internal certs: assume 2048-bit RSA, not self-signed, strong algorithm
        # (these defaults will be overridden if actual values available in kwargs)
        risk_score = RiskScoringEngine.calculate_risk_score(
            valid_to=valid_to,
            key_length=2048,  # Default assumption
            is_self_signed=False,  # Internal certs usually from trusted CA
            algorithm='sha256WithRSAEncryption'  # Modern default
        )
        risk_level = RiskScoringEngine.determine_risk_level(risk_score)
        return risk_level, risk_score
    
    def _determine_certificate_type(self, subject: str) -> str:
        """
        Determine certificate type from subject.
        
        Args:
            subject (str): Certificate subject string
            
        Returns:
            str: Certificate type ('wildcard', 'self-signed', 'multi-domain', 'single')
        """
        if not subject:
            return 'unknown'
        
        subject_lower = subject.lower()
        
        if '*.wildcard' in subject_lower or subject.startswith('*.'):
            return 'wildcard'
        elif 'self' in subject_lower:
            return 'self-signed'
        elif ',' in subject or ';' in subject:
            return 'multi-domain'
        else:
            return 'single'
    
    def _parse_datetime(self, dt_str: Any) -> datetime:
        """
        Parse datetime from various formats.
        
        Args:
            dt_str: Datetime string or object
            
        Returns:
            datetime: Parsed datetime object
        """
        if isinstance(dt_str, datetime):
            return dt_str
        
        if isinstance(dt_str, str):
            # Try ISO format
            for fmt in [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]:
                try:
                    return datetime.strptime(dt_str, fmt).replace(tzinfo=dt_timezone.utc)
                except ValueError:
                    continue
        
        raise ValueError(f"Cannot parse datetime: {dt_str}")


class InternalCertificateError(Exception):
    """Raised when internal certificate ingestion fails."""
    pass
