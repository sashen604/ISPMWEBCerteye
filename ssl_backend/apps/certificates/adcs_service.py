"""
AD CS Integration Service - Orchestrates all AD CS operations.
Handles connection testing, certificate synchronization, risk scoring, and audit logging.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.db import transaction

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
            connector = ADCSConnectorFactory.create_connector(source)
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
                from audit_logs.services import AuditLoggingService
                AuditLoggingService.log_action(
                    action='adcs_connection_test',
                    user=user,
                    description=f"Tested AD CS connection: {source.source_name}",
                    ip_address=ip_address,
                    details={'source_id': source.id, 'success': success}
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
            connector = ADCSConnectorFactory.create_connector(source)
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
                from audit_logs.services import AuditLoggingService
                AuditLoggingService.log_action(
                    action='adcs_sync_completed',
                    user=user,
                    description=f"Synced AD CS certificates from {source.source_name}",
                    ip_address=ip_address,
                    details={
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
            
            if not subject or not thumbprint:
                logger.warning("Certificate missing subject or thumbprint")
                stats['certificates_failed'] += 1
                return
            
            # Check if certificate already exists
            try:
                cert = Certificate.objects.get(thumbprint=thumbprint)
                # Update existing certificate
                cert.common_name = subject.replace('CN=', '').split(',')[0]
                cert.issuer = issuer
                cert.save()
                stats['certificates_updated'] += 1
                stats['imported_thumbprints'].append(thumbprint)
                logger.info(f"Updated existing certificate: {thumbprint}")
                return
            except Certificate.DoesNotExist:
                pass
            
            # Create new certificate
            cert = Certificate.objects.create(
                common_name=subject.replace('CN=', '').split(',')[0],
                subject=subject,
                issuer=issuer,
                thumbprint=thumbprint,
                serial_number=serial_number,
                status='active',
                source='ad_cs'
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
            from risk_engine.services import RiskScoringEngine
            
            # Build certificate info for risk scoring
            cert_info = {
                'common_name': cert.common_name,
                'thumbprint': cert.thumbprint,
                'issuer': cert.issuer,
                'days_until_expiry': 365,  # Could calculate from cert_data
                'key_length': cert_data.get('KeyLength', 2048),
                'signature_algorithm': cert_data.get('SignatureAlgorithm', '')
            }
            
            risk_score = RiskScoringEngine.calculate_risk_score(cert_info)
            cert.risk_level = risk_score['risk_level']
            cert.risk_score = risk_score['risk_score']
            cert.risk_reasoning = risk_score.get('reasoning', {})
            cert.save()
            
            logger.info(f"Risk score calculated for {cert.common_name}: {risk_score['risk_level']}")
        
        except Exception as e:
            logger.error(f"Failed to calculate risk score: {str(e)}")
            # Don't fail the entire certificate import if risk scoring fails
