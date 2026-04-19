"""
Certificate Fetch Service Module

High-level orchestration for SSL/TLS certificate retrieval, parsing, and storage.
Coordinates fetcher and parser modules, handles risk scoring, and manages database operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from django.utils import timezone as django_timezone
from django.db import transaction

from .models import Certificate
from .fetchers import SSLCertificateFetcher, CertificateFetchError
from .parsers import CertificateParser, CertificateParsingError


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
    
    def scan_and_store(self, domain: str, update_if_exists: bool = True) -> Dict[str, Any]:
        """
        Scan a domain for SSL certificate and store in database.
        
        Complete workflow:
        - Fetch certificate from HTTPS domain
        - Parse certificate metadata
        - Calculate risk score
        - Check for duplicates
        - Store or update in database
        
        Args:
            domain (str): Domain to scan (e.g., 'google.com')
            update_if_exists (bool): Update existing certificate if found (default: True)
            
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
            # Step 1: Fetch certificate
            x509_cert, port = self.fetcher.fetch_from_any_port(domain)
            
            # Step 2: Parse certificate
            cert_data = CertificateParser.parse_certificate(x509_cert, domain)
            
            # Step 3: Calculate risk score
            cert_data['risk_level'], cert_data['risk_score'] = self._calculate_risk(cert_data)
            
            # Step 4: Store in database with transaction
            with transaction.atomic():
                certificate, created = self._store_or_update_certificate(
                    cert_data,
                    update_if_exists=update_if_exists
                )
            
            status = 'created' if created else 'updated'
            message = f"Certificate for {domain} {'created' if created else 'updated'} successfully"
            
            return {
                'success': True,
                'message': message,
                'certificate': certificate,
                'status': status,
                'error': None,
            }
            
        except CertificateFetchError as e:
            return {
                'success': False,
                'message': f"Failed to fetch certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
            }
        except CertificateParsingError as e:
            return {
                'success': False,
                'message': f"Failed to parse certificate from {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Unexpected error scanning {domain}",
                'certificate': None,
                'status': 'error',
                'error': str(e),
            }
    
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
        Calculate risk level and risk score for certificate.
        
        Risk Assessment Logic:
        - Risk Score (0-100): Based on days until expiration and key length
          - Days < 7: +50
          - Days < 30: +25
          - Days < 90: +10
          - Key length < 2048: +30
          - Key length < 4096: +10
          - Self-signed: +20
        
        - Risk Level: Categorical classification
          - score > 70: 'critical'
          - score > 50: 'high'
          - score > 25: 'medium'
          - else: 'low'
        
        Args:
            cert_data (dict): Certificate metadata
            
        Returns:
            tuple: (risk_level, risk_score)
        """
        risk_score = 0
        
        # Days remaining scoring
        days_remaining = cert_data.get('days_remaining', 0)
        if days_remaining < 7:
            risk_score += 50
        elif days_remaining < 30:
            risk_score += 25
        elif days_remaining < 90:
            risk_score += 10
        
        # Key length scoring
        key_length = cert_data.get('key_length', 0)
        if key_length < 2048:
            risk_score += 30
        elif key_length < 4096:
            risk_score += 10
        
        # Certificate type scoring
        cert_type = cert_data.get('certificate_type', '')
        if cert_type == 'self-signed':
            risk_score += 20
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine risk level
        if risk_score > 70:
            risk_level = 'critical'
        elif risk_score > 50:
            risk_level = 'high'
        elif risk_score > 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return risk_level, risk_score
