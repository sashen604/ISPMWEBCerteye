"""
AD CS Integration Service - Orchestrates all AD CS operations.
Handles connection testing, certificate synchronization, risk scoring, and audit logging.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models_adcs import (
    ADCSSource, ADCSSyncHistory, ADCSConnectionTest, ADCSCertificate
)
from .models import Certificate
from .adcs_connector import ADCSConnectorFactory
from .adcs_crypto import ADCSCredentialEncryption

logger = logging.getLogger(__name__)


class ADCSIntegrationService:
    """
    High-level service for AD CS integration.
    """
    
    @staticmethod
    def test_connection(source: ADCSSource, user=None, ip_address=None) -> Dict:
        """
        Test AD CS connectivity and store results.
        """
        try:
            # Decrypt password for connection
            try:
                password = ADCSCredentialEncryption.decrypt(source.encrypted_password)
            except Exception as e:
                logger.error(f"Failed to decrypt password: {str(e)}")
                return {
                    'success': False,
                    'message': 'Failed to decrypt credentials',
                    'details': []
                }
            
            # Create connector and test
            connector = ADCSConnectorFactory.create_connector(source, password=password)
            success, message = connector.test_connection()
            connector.close()
            
            # Store connection test result
            test_result = ADCSConnectionTest.objects.create(
                source=source,
                test_results={
                    'timestamp': timezone.now().isoformat(),
                    'auth_type': source.auth_type,
                    'server': source.server_hostname,
                    'ca_name': source.ca_name
                },
                overall_status='connected' if success else 'failed',
                message=message
            )
            
            # Update source status
            if success:
                source.connection_status = 'connected'
            else:
                source.connection_status = 'error'
            source.save()
            
            # Audit log
            if user:
                from apps.audit_logs.services import AuditLoggingService
                AuditLoggingService.log_action(
                    user=user,
                    action='adcs_connection_test',
                    target_type='adcs_source',
                    target_id=source.id,
                    details={
                        'source_name': source.source_name,
                        'description': f"Tested AD CS connection: {source.source_name}",
                        'ip_address': ip_address,
                        'success': success,
                    },
                )
            
            logger.info(f"AD CS connection test {'successful' if success else 'failed'}: {source.source_name}")
            
            return {
                'success': success,
                'message': message,
                'test_id': test_result.id,
                'timestamp': test_result.created_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            source.connection_status = 'error'
            source.save()
            
            return {
                'success': False,
                'message': f'Error during connection test: {str(e)}',
                'details': []
            }
    
    @staticmethod
    @transaction.atomic
    def sync_certificates(source: ADCSSource, user=None, ip_address=None) -> Dict:
        """
        Fetch certificates from AD CS and import to CertEye.
        """
        sync_start = timezone.now()
        stats = {
            'certificates_fetched': 0,
            'certificates_imported': 0,
            'certificates_updated': 0,
            'certificates_failed': 0,
            'imported_thumbprints': []
        }
        
        try:
            # First, test connection
            connection_status = ADCSIntegrationService.test_connection(source, user, ip_address)
            if not connection_status['success']:
                logger.warning(f"Cannot sync - connection test failed: {source.source_name}")
                return {
                    'success': False,
                    'message': 'Connection test failed before sync',
                    'stats': stats
                }
            
            # Decrypt password
            try:
                password = ADCSCredentialEncryption.decrypt(source.encrypted_password)
            except Exception as e:
                logger.error(f"Failed to decrypt password: {str(e)}")
                return {
                    'success': False,
                    'message': 'Failed to decrypt credentials',
                    'stats': stats
                }
            
            # Create connector and fetch certificates
            connector = ADCSConnectorFactory.create_connector(source, password=password)
            certificates = connector.fetch_certificates()
            connector.close()
            
            stats['certificates_fetched'] = len(certificates)
            logger.info(f"Fetched {len(certificates)} certificates from {source.source_name}")
            
            # Process each certificate
            for cert_data in certificates:
                try:
                    ADCSIntegrationService._process_certificate(
                        cert_data, source, stats
                    )
                except Exception as e:
                    logger.error(f"Failed to process certificate: {str(e)}")
                    stats['certificates_failed'] += 1
            
            # Record sync history
            sync_duration = (timezone.now() - sync_start).total_seconds()
            
            sync_history = ADCSSyncHistory.objects.create(
                source=source,
                status='success',
                certificates_fetched=stats['certificates_fetched'],
                certificates_imported=stats['certificates_imported'],
                certificates_updated=stats['certificates_updated'],
                certificates_failed=stats['certificates_failed'],
                duration_seconds=int(sync_duration),
                sync_details={
                    'auth_type': source.auth_type,
                    'server': source.server_hostname,
                    'ca_name': source.ca_name,
                    'imported_thumbprints': stats['imported_thumbprints'][:10]  # Limit for storage
                },
                completed_at=timezone.now()
            )
            
            # Update source certificate count and last sync
            source.certificate_count = stats['certificates_imported']
            source.last_sync_at = timezone.now()
            source.connection_status = 'connected'
            source.save()
            
            # Audit log
            if user:
                from apps.audit_logs.services import AuditLoggingService
                AuditLoggingService.log_action(
                    user=user,
                    action='adcs_sync_completed',
                    target_type='adcs_source',
                    target_id=source.id,
                    details={
                        'source_name': source.source_name,
                        'description': f"Synced AD CS certificates from {source.source_name}",
                        'ip_address': ip_address,
                        'source_id': source.id,
                        'sync_history_id': sync_history.id,
                        'stats': stats
                    }
                )
            
            logger.info(f"AD CS sync completed: {stats['certificates_imported']} imported, {stats['certificates_failed']} failed")
            
            return {
                'success': True,
                'message': f"Sync completed: {stats['certificates_imported']} imported, {stats['certificates_failed']} failed",
                'stats': stats,
                'sync_history_id': sync_history.id,
                'duration_seconds': int(sync_duration)
            }
        
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            
            sync_duration = (timezone.now() - sync_start).total_seconds()
            sync_history = ADCSSyncHistory.objects.create(
                source=source,
                status='failed',
                certificates_fetched=0,
                certificates_imported=0,
                certificates_updated=0,
                certificates_failed=0,
                duration_seconds=int(sync_duration),
                error_message=str(e),
                completed_at=timezone.now()
            )
            
            source.connection_status = 'error'
            source.save()
            
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'stats': stats,
                'sync_history_id': sync_history.id
            }
    
    @staticmethod
    def _process_certificate(cert_data: Dict, source: ADCSSource, stats: Dict):
        """
        Process a single certificate from AD CS.
        """
        try:
            # Extract certificate information
            subject = cert_data.get('Subject', '')
            thumbprint = cert_data.get('Thumbprint', '').replace(' ', '')
            issuer = cert_data.get('Issuer', '')
            serial_number = cert_data.get('SerialNumber', '')
            signature_algorithm = cert_data.get('SignatureAlgorithm', 'Unknown') or 'Unknown'

            key_length_raw = cert_data.get('KeyLength', 2048)
            try:
                key_length = int(key_length_raw) if key_length_raw is not None else 2048
            except (TypeError, ValueError):
                key_length = 2048

            valid_from = ADCSIntegrationService._parse_datetime(cert_data.get('NotBefore'))
            valid_to = ADCSIntegrationService._parse_datetime(cert_data.get('NotAfter'))
            now = timezone.now()
            days_remaining = max(0, (valid_to - now).days)

            domain = ADCSIntegrationService._extract_primary_name(subject)
            risk_level, risk_score, risk_reasoning = ADCSIntegrationService._calculate_risk_fields(
                valid_to=valid_to,
                key_length=key_length,
                issuer=issuer,
                subject=subject,
                signature_algorithm=signature_algorithm,
            )
            
            if not subject or not thumbprint:
                logger.warning("Certificate missing subject or thumbprint")
                stats['certificates_failed'] += 1
                return

            cert_defaults = {
                'domain': domain,
                'hostname': source.server_hostname,
                'certificate_type': 'single',
                'issuer': issuer,
                'subject': subject,
                'serial_number': serial_number or thumbprint[:64],
                'signature_algorithm': signature_algorithm,
                'key_length': key_length,
                'valid_from': valid_from,
                'valid_to': valid_to,
                'days_remaining': days_remaining,
                'risk_level': risk_level,
                'risk_score': risk_score,
                'risk_reasoning': risk_reasoning,
                'source_type': 'adcs',
                'status': 'active' if valid_to > now else 'expired',
                'template_name': cert_data.get('Template', '') or '',
                'last_scanned': now,
                'is_self_signed': issuer.strip() == subject.strip(),
            }
            
            # Check if certificate already exists
            try:
                cert = Certificate.objects.get(thumbprint=thumbprint)
                # Update existing certificate
                for field_name, field_value in cert_defaults.items():
                    setattr(cert, field_name, field_value)
                cert.save()
                stats['certificates_updated'] += 1
                stats['imported_thumbprints'].append(thumbprint)
                logger.info(f"Updated existing certificate: {thumbprint}")
                return
            except Certificate.DoesNotExist:
                pass
            
            # Create new certificate
            cert = Certificate.objects.create(
                thumbprint=thumbprint,
                **cert_defaults,
            )
            
            # Create AD CS specific metadata
            dns_names = cert_data.get('dns_names', [])
            if isinstance(dns_names, str):
                dns_names = [dns_names]
            
            ADCSCertificate.objects.create(
                certificate=cert,
                source=source,
                request_id=cert_data.get('request_id', ''),
                template_name=cert_data.get('Template', ''),
                requester=cert_data.get('Requester', ''),
                approver=cert_data.get('Approver', ''),
                dns_names=dns_names,
                issued_at=timezone.now()  # Could parse from cert_data if available
            )
            
            # Calculate risk score
            ADCSIntegrationService._calculate_risk_score(cert, cert_data)
            
            stats['certificates_imported'] += 1
            stats['imported_thumbprints'].append(thumbprint)
            logger.info(f"Imported new certificate: {thumbprint}")
        
        except Exception as e:
            logger.error(f"Error processing certificate {cert_data.get('Thumbprint', 'unknown')}: {str(e)}")
            stats['certificates_failed'] += 1
            raise
    
    @staticmethod
    def _calculate_risk_score(cert: Certificate, cert_data: Dict):
        """
        Calculate and assign risk score to certificate.
        """
        try:
            risk_level, risk_score, risk_reasoning = ADCSIntegrationService._calculate_risk_fields(
                valid_to=cert.valid_to,
                key_length=cert_data.get('KeyLength') or cert.key_length,
                issuer=cert.issuer,
                subject=cert.subject,
                signature_algorithm=cert_data.get('SignatureAlgorithm') or cert.signature_algorithm,
            )
            cert.risk_level = risk_level
            cert.risk_score = risk_score
            cert.risk_reasoning = risk_reasoning
            cert.save()
            
            logger.info(f"Risk score calculated for {cert.domain}: {risk_level}")
        
        except Exception as e:
            logger.error(f"Failed to calculate risk score: {str(e)}")
            # Don't fail the entire certificate import if risk scoring fails

    @staticmethod
    def _parse_datetime(raw_value) -> datetime:
        if isinstance(raw_value, datetime):
            dt = raw_value
        else:
            dt = parse_datetime(str(raw_value)) if raw_value else None

        if dt is None:
            dt = timezone.now()

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    @staticmethod
    def _extract_primary_name(subject: str) -> str:
        if not subject:
            return 'unknown.local'

        for part in subject.split(','):
            item = part.strip()
            if item.upper().startswith('CN='):
                return item[3:].strip() or 'unknown.local'

        return subject.strip() or 'unknown.local'

    @staticmethod
    def _calculate_risk_fields(
        valid_to: datetime,
        key_length,
        issuer: str,
        subject: str,
        signature_algorithm: str,
    ) -> Tuple[str, int, Dict]:
        from apps.risk_engine.services import RiskScoringEngine

        try:
            key_length_int = int(key_length)
        except (TypeError, ValueError):
            key_length_int = 2048

        is_self_signed = (issuer or '').strip() == (subject or '').strip()
        score = RiskScoringEngine.calculate_risk_score(
            valid_to=valid_to,
            key_length=key_length_int,
            is_self_signed=is_self_signed,
            algorithm=signature_algorithm,
        )
        level = RiskScoringEngine.determine_risk_level(score)
        reasoning = RiskScoringEngine.get_risk_reasoning(
            valid_to=valid_to,
            key_length=key_length_int,
            is_self_signed=is_self_signed,
            algorithm=signature_algorithm,
        )
        return level, score, reasoning
