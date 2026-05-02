"""
Certificate Fetch Service Module

High-level orchestration for SSL/TLS certificate retrieval, parsing, and storage.
Coordinates fetcher and parser modules, handles risk scoring, and manages database operations.
"""

from typing import Optional, Dict, Any

from django.utils import timezone as django_timezone
from django.db import transaction

from apps.certificates.models import Certificate, Domain, DomainScanHistory
from apps.certificates.fetchers import (
    SSLCertificateFetcher,
    CertificateFetchError,
    ConnectionTimeoutError,
    DNSResolutionError,
    InvalidCertificateError,
    clean_domain,
)
from apps.certificates.parsers import CertificateParser, CertificateParsingError
from apps.certificates.crypto_health import analyze_certificate_health
from apps.risk_engine.services import RiskScoringEngine
from apps.audit_logs.services import AuditLoggingService
from apps.alerts.services import AlertEngine


class CertificateFetchService:
    """
    Orchestrates SSL certificate retrieval, parsing, and database storage.
    
    Workflow:
    1. Fetch certificate from domain using SSLCertificateFetcher
    2. Parse certificate metadata using CertificateParser
    3. Calculate risk scores
    4. Check for duplicates (by serial number)
    5. Store or update in database with transaction safety
    
    Attributes:
        fetcher (SSLCertificateFetcher): Low-level certificate fetcher
        timeout (int): Connection timeout in seconds
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize certificate fetch service.
        
        Args:
            timeout (int): Connection timeout in seconds (default: 10)
        """
        self.fetcher = SSLCertificateFetcher(timeout=timeout)
        self.timeout = timeout
    
    def scan_and_store(
        self,
        domain: str,
        update_if_exists: bool = True,
        user=None,
        request=None,
        domain_obj: Optional[Domain] = None,
    ) -> Dict[str, Any]:
        """
        Scan a domain for SSL certificate and store in database.
        
        Complete workflow:
        - Fetch certificate from HTTPS domain
        - Parse certificate metadata
        - Calculate risk score
        - Check for duplicates
        - Store or update in database
        
        Args:
            domain (str): Domain to scan (e.g., 'google.com' or 'https://www.google.com/')
            update_if_exists (bool): Update existing certificate if found (default: True)
            user: User object for audit logging
            request: HTTP request object for IP extraction
            
        Returns:
            dict: Result dictionary with:
                - success (bool): Whether operation succeeded
                - message (str): Human-readable message
                - certificate (Certificate): Stored certificate object (if successful)
                - error (str): Error message (if failed)
                - status (str): 'created', 'updated', or 'error'
                
        Example:
            >>> service = CertificateFetchService()
            >>> result = service.scan_and_store('google.com')
            >>> if result['success']:
            ...     cert = result['certificate']
            ...     print(f"Scanned {cert.domain}: expires in {cert.days_remaining} days")
        """
        try:
            # Clean domain input (handles URLs, www prefixes, etc.)
            domain = clean_domain(domain)
            
            if not domain:
                return {
                    'success': False,
                    'message': 'Invalid domain name',
                    'certificate': None,
                    'error': 'Domain name cannot be empty',
                    'status': 'error'
                }
            
            # Step 1: Fetch certificate
            x509_cert, port = self.fetcher.fetch_from_any_port(domain)
            
            # Step 2: Parse certificate
            cert_data = CertificateParser.parse_certificate(x509_cert, domain)

            # Step 3: Analyze cryptographic health (for score + explainability)
            cert_data['crypto_findings'] = self._extract_crypto_findings(x509_cert)

            # Step 4: Calculate weighted risk score + reasons
            cert_data['risk_level'], cert_data['risk_score'], cert_data['risk_reasoning'] = self._calculate_risk(cert_data)
            
            # Step 5: Store in database with transaction
            with transaction.atomic():
                certificate, created = self._store_or_update_certificate(
                    cert_data,
                    update_if_exists=update_if_exists
                )
            
            # Step 6: Log certificate action
            try:
                if created:
                    AuditLoggingService.log_certificate_action(
                        user=user,
                        action='create',
                        certificate_id=certificate.id,
                        certificate_name=certificate.subject or domain,
                        domain=domain,
                        new_values={
                            'issuer': certificate.issuer,
                            'valid_from': str(certificate.valid_from),
                            'valid_to': str(certificate.valid_to),
                            'key_length': certificate.key_length,
                            'risk_level': certificate.risk_level,
                        },
                        request=request,
                    )
                else:
                    AuditLoggingService.log_certificate_action(
                        user=user,
                        action='update',
                        certificate_id=certificate.id,
                        certificate_name=certificate.subject or domain,
                        domain=domain,
                        new_values={
                            'issuer': certificate.issuer,
                            'valid_to': str(certificate.valid_to),
                            'risk_level': certificate.risk_level,
                        },
                        request=request,
                    )
            except Exception as log_error:
                # Log error if audit logging fails but don't fail the operation
                import sys
                print(f"ERROR: Audit logging failed: {log_error}", file=sys.stderr)
            
            status = 'created' if created else 'updated'
            message = f"Certificate for {domain} {'created' if created else 'updated'} successfully"
            response = {
                'success': True,
                'message': message,
                'certificate': certificate,
                'status': status,
                'error': None,
            }
            try:
                AlertEngine().trigger_risk_alert(certificate, trigger_source='immediate')
            except Exception:
                # Alerting must not block certificate ingestion.
                pass
            self._create_scan_history(
                domain_obj,
                {
                    "success": True,
                    "certificate": certificate,
                    "risk_score": certificate.risk_score,
                    "risk_level": certificate.risk_level,
                    "risk_reasoning": certificate.risk_reasoning,
                    "parsed_data": cert_data,
                },
            )
            return response
            
        except ConnectionTimeoutError as e:
            failure = {
                'success': False,
                'message': f"Failed to fetch certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'timeout',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
        except DNSResolutionError as e:
            failure = {
                'success': False,
                'message': f"Failed to fetch certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'invalid_domain',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
        except InvalidCertificateError as e:
            failure = {
                'success': False,
                'message': f"Failed to fetch certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'ssl_error',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
        except CertificateFetchError as e:
            failure = {
                'success': False,
                'message': f"Failed to fetch certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'fetch_error',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
        except CertificateParsingError as e:
            failure = {
                'success': False,
                'message': f"Failed to parse certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'parse_error',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
        except Exception as e:
            failure = {
                'success': False,
                'message': f"Unexpected error scanning {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
                'error_type': 'unexpected_error',
            }
            self._create_scan_history(domain_obj, failure)
            return failure
    
    def scan_multiple(self, domains: list, update_if_exists: bool = True) -> Dict[str, Any]:
        """
        Scan multiple domains and return aggregated results.
        
        Args:
            domains (list): List of domain names
            update_if_exists (bool): Update existing certificates if found
            
        Returns:
            dict: Aggregated results:
                - total (int): Total domains scanned
                - succeeded (int): Successfully scanned
                - failed (int): Failed scans
                - created (int): New certificates created
                - updated (int): Existing certificates updated
                - results (list): Individual result dictionaries
        """
        results = []
        succeeded = 0
        failed = 0
        created = 0
        updated = 0
        
        for domain in domains:
            result = self.scan_and_store(domain, update_if_exists=update_if_exists)
            results.append(result)
            
            if result['success']:
                succeeded += 1
                if result['status'] == 'created':
                    created += 1
                elif result['status'] == 'updated':
                    updated += 1
            else:
                failed += 1
        
        return {
            'total': len(domains),
            'succeeded': succeeded,
            'failed': failed,
            'created': created,
            'updated': updated,
            'results': results,
        }
    
    def _store_or_update_certificate(
        self,
        cert_data: Dict[str, Any],
        update_if_exists: bool = True
    ) -> tuple:
        """
        Store certificate in database or update if exists.
        
        Checks for existing certificate by serial number.
        If found and update_if_exists=True, updates existing record.
        Otherwise creates new record.
        
        Args:
            cert_data (dict): Certificate metadata from parser
            update_if_exists (bool): Whether to update existing certificates
            
        Returns:
            tuple: (Certificate object, created flag)
        """
        serial_number = cert_data['serial_number']
        domain = cert_data['domain']
        
        # Try to find existing certificate by serial number
        try:
            cert = Certificate.objects.get(serial_number=serial_number)
            
            if update_if_exists:
                # Update existing certificate
                for key, value in cert_data.items():
                    setattr(cert, key, value)
                cert.save()
                return cert, False
            else:
                # Return existing without update
                return cert, False
                
        except Certificate.DoesNotExist:
            # Create new certificate
            cert = Certificate.objects.create(**cert_data)
            return cert, True
    
    def _calculate_risk(self, cert_data: Dict[str, Any]) -> tuple:
        """
        Calculate risk level and risk score using unified risk engine.
        
        Args:
            cert_data (dict): Certificate metadata including:
                - valid_to: Certificate expiration datetime
                - key_length: RSA key length in bits
                - certificate_type: Type of certificate ('self-signed', etc)
                - signature_algorithm: Signature algorithm
            
        Returns:
            tuple: (risk_level, risk_score)
                - risk_level: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW' (uppercase)
                - risk_score: 0-100 integer
        """
        # Extract certificate properties
        valid_to = cert_data.get('valid_to')
        key_length = cert_data.get('key_length', 2048)
        cert_type = cert_data.get('certificate_type', '')
        algorithm = cert_data.get('signature_algorithm', '')
        
        # Determine if self-signed
        is_self_signed = cert_type == 'self-signed'
        
        days_remaining = cert_data.get("days_remaining", 0)
        crypto_findings = cert_data.get("crypto_findings", {})

        weighted = RiskScoringEngine.calculate_weighted_risk(
            days_remaining=days_remaining,
            valid_to=valid_to,
            key_length=key_length,
            is_self_signed=is_self_signed,
            algorithm=algorithm,
            crypto_findings=crypto_findings,
            valid_from=cert_data.get("valid_from"),
        )
        return weighted["risk_level"], weighted["total_score"], weighted

    def _extract_crypto_findings(self, x509_cert) -> Dict[str, Any]:
        """Run crypto health analysis and fail-safe on parser issues."""
        try:
            cert_obj = x509_cert.to_cryptography()
            return analyze_certificate_health(cert_obj)
        except Exception as exc:
            return {
                "issues": [f"Failed to analyze crypto health: {exc}"],
                "is_weak_algorithm": False,
                "is_weak_key": False,
            }

    def _create_scan_history(self, domain_obj: Optional[Domain], result: Dict[str, Any]) -> None:
        """Persist scan history rows for managed domains only."""
        if not domain_obj:
            return

        now = django_timezone.now()
        certificate = result.get("certificate")
        is_success = bool(result.get("success"))

        DomainScanHistory.objects.create(
            domain=domain_obj,
            scanned_at=now,
            status=DomainScanHistory.STATUS_SUCCESS if is_success else DomainScanHistory.STATUS_FAILED,
            error_message=None if is_success else result.get("error"),
            certificate=certificate,
            parsed_data=result.get("parsed_data", {}),
            risk_score=result.get("risk_score", getattr(certificate, "risk_score", 0) or 0),
            risk_level=result.get("risk_level", getattr(certificate, "risk_level", "") or ""),
            risk_reasoning=result.get("risk_reasoning", getattr(certificate, "risk_reasoning", {}) or {}),
        )
        domain_obj.last_scan_at = now
        domain_obj.last_status = "success" if is_success else "failed"
        domain_obj.save(update_fields=["last_scan_at", "last_status", "updated_at"])
