from django.utils import timezone
from django.db.models import Q, Count, Case, When, Value, CharField
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
import csv
import json

from .models import Certificate, Domain, DomainScanHistory
from .serializers import (
    CertificateSerializer,
    DomainSerializer,
    DomainScanHistorySerializer,
    InternalCertificatePayloadSerializer,
    InternalCertificateBatchSerializer,
    InternalCertificateIngestionResponseSerializer,
    InternalCertificateBatchResponseSerializer
)
from .services import CertificateFetchService
from .internal_service import InternalCertificateService, InternalCertificateError
from .agent_auth import CertificateAgent, AgentAuditLog, AgentRateLimiter
from apps.audit_logs.services import AuditLoggingService
from apps.authentication.permissions import IsAdminOrReadOnly, IsAdminOrSuperAdmin


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['issuer', 'key_length', 'status', 'source_type', 'risk_level']
    search_fields = ['domain', 'hostname', 'issuer', 'subject']
    ordering_fields = ['domain', 'risk_level', 'valid_to', 'created_at', 'days_remaining']
    ordering = ['valid_to']

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        domain = params.get('domain')
        if domain:
            queryset = queryset.filter(domain__icontains=domain)

        risk_level = params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level__iexact=risk_level)

        certificate_type = params.get('certificate_type')
        if certificate_type:
            queryset = queryset.filter(certificate_type__iexact=certificate_type)

        source_type = params.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type__iexact=source_type)

        expiration_status = params.get('expiration_status')
        if expiration_status:
            now = timezone.now()
            if expiration_status.lower() == 'expired':
                queryset = queryset.filter(valid_to__lt=now)
            elif expiration_status.lower() == 'active':
                queryset = queryset.filter(valid_to__gte=now)
            elif expiration_status.lower() == 'expiring_soon':
                threshold_days = int(params.get('expiring_days', 30))
                threshold = now + timezone.timedelta(days=threshold_days)
                queryset = queryset.filter(valid_to__gte=now, valid_to__lte=threshold)

        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def scan(self, request):
        """
        Scan a domain for SSL/TLS certificate and store in database.
        
        Request body:
        {
            "domain": "example.com",
            "timeout": 10,  # Optional, default 10
            "update_if_exists": true  # Optional, default true
        }
        
        Response:
        {
            "success": true,
            "message": "Certificate for example.com created successfully",
            "status": "created",  # or "updated"
            "certificate": { ... },
            "error": null
        }
        """
        domain = request.data.get('domain')
        timeout = request.data.get('timeout', 10)
        update_if_exists = request.data.get('update_if_exists', True)
        
        if not domain:
            return Response(
                {
                    'success': False,
                    'message': 'Domain is required',
                    'error': 'Missing required field: domain'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize service
        service = CertificateFetchService(timeout=timeout)
        
        # Scan and store certificate (with audit logging)
        result = service.scan_and_store(
            domain,
            update_if_exists=update_if_exists,
            user=request.user,
            request=request,
        )
        
        if result['success']:
            # Serialize the certificate
            serializer = self.get_serializer(result['certificate'])
            return Response(
                {
                    'success': True,
                    'message': result['message'],
                    'status': result['status'],
                    'certificate': serializer.data,
                    'error': None
                },
                status=status.HTTP_201_CREATED if result['status'] == 'created' else status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'message': result['message'],
                    'status': 'error',
                    'certificate': None,
                    'error': result['error']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a certificate and log the action."""
        certificate = self.get_object()
        cert_data = {
            'id': certificate.id,
            'domain': certificate.domain,
            'issuer': certificate.issuer,
            'valid_from': str(certificate.valid_from),
            'valid_to': str(certificate.valid_to),
            'key_length': certificate.key_length,
            'risk_level': certificate.risk_level,
        }
        
        # Log the deletion
        try:
            AuditLoggingService.log_certificate_action(
                user=request.user,
                action='delete',
                certificate_id=certificate.id,
                certificate_name=certificate.subject or certificate.domain,
                domain=certificate.domain,
                old_values=cert_data,
                request=request,
            )
        except Exception:
            # Don't fail the deletion if logging fails
            pass
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def scan_batch(self, request):
        """
        Scan multiple domains for SSL/TLS certificates.
        
        Request body:
        {
            "domains": ["example.com", "google.com", "github.com"],
            "timeout": 10,  # Optional, default 10
            "update_if_exists": true  # Optional, default true
        }
        
        Response:
        {
            "total": 3,
            "succeeded": 2,
            "failed": 1,
            "created": 2,
            "updated": 0,
            "results": [ ... ]
        }
        """
        domains = request.data.get('domains', [])
        timeout = request.data.get('timeout', 10)
        update_if_exists = request.data.get('update_if_exists', True)
        
        if not domains or not isinstance(domains, list):
            return Response(
                {
                    'success': False,
                    'message': 'Domains list is required',
                    'error': 'Missing or invalid required field: domains (must be a list)'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize service
        service = CertificateFetchService(timeout=timeout)
        
        # Scan multiple domains
        results = service.scan_multiple(domains, update_if_exists=update_if_exists)
        
        # Serialize successful certificates
        for result in results['results']:
            if result['success']:
                serializer = self.get_serializer(result['certificate'])
                result['certificate'] = serializer.data
        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def collect_internal(self, request):
        """
        Collect certificates from internal sources (PowerShell agents).
        
        Supports both single certificate and batch ingestion.
        
        Single Certificate:
        POST /api/certificates/collect_internal/
        {
            "hostname": "SERVER01",
            "subject": "*.example.com",
            "issuer": "Internal CA",
            "thumbprint": "ABCD1234...",
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_to": "2025-01-01T00:00:00Z",
            "certificate_template": "WebServer",
            "agent_token": "token_here"
        }
        
        Batch:
        POST /api/certificates/collect_internal/
        {
            "certificates": [...],
            "agent_token": "token_here"
        }
        """
        agent_token = request.data.get('agent_token')
        if not agent_token:
            # Log unauthorized attempt
            AgentAuditLog.objects.create(
                status='unauthorized',
                ip_address=self._get_client_ip(request),
                error_message='Missing agent token'
            )
            return Response(
                {
                    'success': False,
                    'message': 'Agent token required',
                    'error': 'Missing required field: agent_token'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Authenticate agent
        try:
            agent = CertificateAgent.objects.get(token=agent_token)
            if not agent.is_token_valid():
                AgentAuditLog.objects.create(
                    agent=agent,
                    status='unauthorized',
                    ip_address=self._get_client_ip(request),
                    error_message='Invalid or expired token'
                )
                return Response(
                    {
                        'success': False,
                        'message': 'Invalid or expired agent token',
                        'error': 'Token validation failed'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except CertificateAgent.DoesNotExist:
            AgentAuditLog.objects.create(
                status='unauthorized',
                ip_address=self._get_client_ip(request),
                error_message='Unknown agent token'
            )
            return Response(
                {
                    'success': False,
                    'message': 'Unknown agent token',
                    'error': 'Agent not found'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Determine if single or batch
        is_batch = 'certificates' in request.data
        
        try:
            if is_batch:
                return self._handle_batch_ingestion(request, agent)
            else:
                return self._handle_single_ingestion(request, agent)
        except Exception as e:
            error_msg = str(e)
            AgentAuditLog.objects.create(
                agent=agent,
                status='failed',
                ip_address=self._get_client_ip(request),
                error_message=error_msg
            )
            return Response(
                {
                    'success': False,
                    'message': 'Error processing certificate',
                    'error': error_msg
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _handle_single_ingestion(self, request, agent: CertificateAgent):
        """Handle single certificate ingestion."""
        serializer = InternalCertificatePayloadSerializer(data=request.data)
        
        if not serializer.is_valid():
            AgentAuditLog.objects.create(
                agent=agent,
                status='malformed',
                ip_address=self._get_client_ip(request),
                error_message=str(serializer.errors)
            )
            return Response(
                {
                    'success': False,
                    'message': 'Invalid certificate payload',
                    'error': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check rate limit
        is_allowed, rate_limit_msg = AgentRateLimiter.check_rate_limit(agent.agent_id, 1)
        if not is_allowed:
            return Response(
                {
                    'success': False,
                    'message': rate_limit_msg,
                    'error': 'Rate limit exceeded'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        try:
            service = InternalCertificateService()
            certificate, created, status_msg = service.ingest_certificate(
                hostname=serializer.validated_data['hostname'],
                subject=serializer.validated_data['subject'],
                issuer=serializer.validated_data['issuer'],
                thumbprint=serializer.validated_data['thumbprint'],
                valid_from=serializer.validated_data.get('valid_from'),
                valid_to=serializer.validated_data['valid_to'],
                certificate_template=serializer.validated_data.get('certificate_template'),
                agent_id=agent.agent_id,
                signature_algorithm=serializer.validated_data.get('signature_algorithm'),
                key_length=serializer.validated_data.get('key_length', 2048),
            )
            
            AgentRateLimiter.record_submission(agent.agent_id, 1)
            agent.record_submission(1)
            
            # Log success
            AgentAuditLog.objects.create(
                agent=agent,
                status='success',
                ip_address=self._get_client_ip(request),
                certificates_submitted=1,
                certificates_created=1 if created else 0,
                certificates_updated=0 if created else 1,
            )
            
            cert_serializer = CertificateSerializer(certificate)
            return Response(
                {
                    'success': True,
                    'message': f"Certificate {'created' if created else 'updated'}: {certificate.hostname}/{certificate.subject}",
                    'status': 'created' if created else 'updated',
                    'certificate': cert_serializer.data,
                    'error': None
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except InternalCertificateError as e:
            error_msg = str(e)
            AgentAuditLog.objects.create(
                agent=agent,
                status='failed',
                ip_address=self._get_client_ip(request),
                certificates_submitted=1,
                certificates_failed=1,
                error_message=error_msg
            )
            return Response(
                {
                    'success': False,
                    'message': 'Error ingesting certificate',
                    'error': error_msg
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _handle_batch_ingestion(self, request, agent: CertificateAgent):
        """Handle batch certificate ingestion."""
        serializer = InternalCertificateBatchSerializer(data=request.data)
        
        if not serializer.is_valid():
            AgentAuditLog.objects.create(
                agent=agent,
                status='malformed',
                ip_address=self._get_client_ip(request),
                error_message=str(serializer.errors)
            )
            return Response(
                {
                    'success': False,
                    'message': 'Invalid batch payload',
                    'error': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificates = serializer.validated_data['certificates']
        update_if_exists = serializer.validated_data.get('update_if_exists', True)
        
        # Check rate limit
        is_allowed, rate_limit_msg = AgentRateLimiter.check_rate_limit(
            agent.agent_id,
            len(certificates)
        )
        if not is_allowed:
            return Response(
                {
                    'success': False,
                    'message': rate_limit_msg,
                    'error': 'Rate limit exceeded'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        try:
            service = InternalCertificateService()
            results = service.ingest_batch(
                certificates=certificates,
                agent_id=agent.agent_id,
                update_if_exists=update_if_exists
            )
            
            # Record with rate limiter
            AgentRateLimiter.record_submission(agent.agent_id, len(certificates))
            agent.record_submission(len(certificates))
            
            # Log batch results
            status_type = 'success' if results['failed'] == 0 else 'partial'
            AgentAuditLog.objects.create(
                agent=agent,
                status=status_type,
                ip_address=self._get_client_ip(request),
                certificates_submitted=results['total'],
                certificates_created=results['created'],
                certificates_updated=results['updated'],
                certificates_failed=results['failed'],
            )
            
            # Serialize certificates in results
            for result in results['results']:
                if result['success'] and result['certificate']:
                    result['certificate'] = CertificateSerializer(result['certificate']).data
            
            return Response(
                {
                    'success': results['failed'] == 0,
                    'message': f"Batch processed: {results['created']} created, {results['updated']} updated, {results['failed']} failed",
                    'status': status_type,
                    'total': results['total'],
                    'created': results['created'],
                    'updated': results['updated'],
                    'failed': results['failed'],
                    'results': results['results'],
                    'error': None
                },
                status=status.HTTP_201_CREATED if results['created'] > 0 else status.HTTP_200_OK
            )
            
        except Exception as e:
            error_msg = str(e)
            AgentAuditLog.objects.create(
                agent=agent,
                status='failed',
                ip_address=self._get_client_ip(request),
                certificates_submitted=len(certificates),
                certificates_failed=len(certificates),
                error_message=error_msg
            )
            return Response(
                {
                    'success': False,
                    'message': 'Error processing batch',
                    'error': error_msg
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request):
        """
        Get certificate statistics for dashboard.
        
        Returns:
        {
            "total_certificates": 150,
            "by_risk_level": {
                "CRITICAL": 5,
                "HIGH": 12,
                "MEDIUM": 28,
                "LOW": 105
            },
            "by_source_type": {
                "scanner": 100,
                "internal_agent": 50
            },
            "expiration_stats": {
                "expired": 2,
                "expiring_soon": 8,
                "active": 140
            },
            "by_certificate_type": {
                "wildcard": 30,
                "self-signed": 5,
                "single": 115
            }
        }
        """
        now = timezone.now()
        expiring_days = int(request.query_params.get('expiring_days', 30))
        expiring_threshold = now + timezone.timedelta(days=expiring_days)
        
        stats = {
            'total_certificates': Certificate.objects.count(),
            'by_risk_level': {
                'CRITICAL': Certificate.objects.filter(risk_level='CRITICAL').count(),
                'HIGH': Certificate.objects.filter(risk_level='HIGH').count(),
                'MEDIUM': Certificate.objects.filter(risk_level='MEDIUM').count(),
                'LOW': Certificate.objects.filter(risk_level='LOW').count(),
            },
            'by_source_type': {
                'scanner': Certificate.objects.filter(source_type='scanner').count(),
                'internal_agent': Certificate.objects.filter(source_type='internal_agent').count(),
            },
            'expiration_stats': {
                'expired': Certificate.objects.filter(valid_to__lt=now).count(),
                'expiring_soon': Certificate.objects.filter(valid_to__gte=now, valid_to__lte=expiring_threshold).count(),
                'active': Certificate.objects.filter(valid_to__gt=expiring_threshold).count(),
            },
            'by_certificate_type': {},
        }
        
        # Certificate type breakdown
        cert_types = Certificate.objects.values('certificate_type').annotate(count=Count('id'))
        for ct in cert_types:
            stats['by_certificate_type'][ct['certificate_type']] = ct['count']
        
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export(self, request):
        """
        Export certificates in CSV or JSON format.
        
        Query parameters:
        - format: 'csv' or 'json' (default: 'csv')
        - filter by standard query parameters (domain, risk_level, etc.)
        
        Returns: CSV file or JSON array
        """
        fmt = request.query_params.get('format', 'csv').lower()
        
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())
        serializer = CertificateSerializer(queryset, many=True)
        data = serializer.data
        
        if fmt == 'json':
            response = HttpResponse(
                json.dumps(data, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = 'attachment; filename="certificates.json"'
            return response
        
        # CSV format (default)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="certificates.csv"'
        
        writer = csv.DictWriter(response, fieldnames=[
            'domain', 'hostname', 'issuer', 'certificate_type', 'subject',
            'serial_number', 'key_length', 'valid_from', 'valid_to',
            'days_remaining', 'risk_level', 'risk_score', 'source_type',
            'status', 'thumbprint', 'template_name', 'created_at'
        ])
        
        writer.writeheader()
        for cert in data:
            writer.writerow({
                'domain': cert.get('domain'),
                'hostname': cert.get('hostname'),
                'issuer': cert.get('issuer'),
                'certificate_type': cert.get('certificate_type'),
                'subject': cert.get('subject'),
                'serial_number': cert.get('serial_number'),
                'key_length': cert.get('key_length'),
                'valid_from': cert.get('valid_from'),
                'valid_to': cert.get('valid_to'),
                'days_remaining': cert.get('days_remaining'),
                'risk_level': cert.get('risk_level'),
                'risk_score': cert.get('risk_score'),
                'source_type': cert.get('source_type'),
                'status': cert.get('status'),
                'thumbprint': cert.get('thumbprint'),
                'template_name': cert.get('template_name'),
                'created_at': cert.get('created_at'),
            })
        
        return response
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def batch_update(self, request):
        """
        Batch update certificates (status, source_priority, etc).
        
        Request body:
        {
            "certificate_ids": [1, 2, 3],
            "updates": {
                "status": "archived",
                "source_priority": 100
            }
        }
        
        Returns: Number of certificates updated
        """
        cert_ids = request.data.get('certificate_ids', [])
        updates = request.data.get('updates', {})
        
        if not cert_ids or not updates:
            return Response(
                {'error': 'certificate_ids and updates are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow certain fields to be updated via batch
        allowed_fields = ['status', 'source_priority']
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not safe_updates:
            return Response(
                {'error': f'No valid fields to update. Allowed: {allowed_fields}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        count = Certificate.objects.filter(id__in=cert_ids).update(**safe_updates)
        
        return Response({
            'success': True,
            'message': f'Updated {count} certificates',
            'updated_count': count
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def find_duplicates(self, request):
        """
        Find potential duplicate certificates (same domain or thumbprint across sources).
        
        Returns: List of certificate groups that may be duplicates
        """
        # Find certs with same domain but different source_type
        domain_duplicates = Certificate.objects.values('domain').annotate(
            count=Count('id'),
            sources=Count('source_type', distinct=True)
        ).filter(sources__gt=1, count__gt=1)
        
        # Find certs with same thumbprint
        thumbprint_duplicates = Certificate.objects.filter(
            thumbprint__isnull=False
        ).values('thumbprint').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicates = {
            'domain_duplicates': [],
            'thumbprint_duplicates': []
        }
        
        for group in domain_duplicates:
            certs = Certificate.objects.filter(domain=group['domain']).values_list('id', 'source_type', 'risk_level')
            duplicates['domain_duplicates'].append({
                'domain': group['domain'],
                'count': group['count'],
                'certificates': [{'id': c[0], 'source_type': c[1], 'risk_level': c[2]} for c in certs]
            })
        
        for group in thumbprint_duplicates:
            certs = Certificate.objects.filter(thumbprint=group['thumbprint']).values_list('id', 'domain', 'source_type')
            duplicates['thumbprint_duplicates'].append({
                'thumbprint': group['thumbprint'],
                'count': group['count'],
                'certificates': [{'id': c[0], 'domain': c[1], 'source_type': c[2]} for c in certs]
            })
        
        return Response(duplicates, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def merge_duplicates(self, request):
        """
        Merge duplicate certificates, keeping the one with highest source_priority.
        
        Request body:
        {
            "primary_id": 1,
            "duplicate_ids": [2, 3]
        }
        
        Returns: Merged certificate details
        """
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])
        
        if not primary_id or not duplicate_ids:
            return Response(
                {'error': 'primary_id and duplicate_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            primary = Certificate.objects.get(id=primary_id)
            duplicates = Certificate.objects.filter(id__in=duplicate_ids)
            
            if not duplicates.exists():
                return Response(
                    {'error': 'No duplicate certificates found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Merge certificate chain data
            chains = []
            for dup in duplicates:
                if dup.certificate_chain:
                    chains.extend(dup.certificate_chain if isinstance(dup.certificate_chain, list) else [dup.certificate_chain])
            
            if chains and primary.certificate_chain:
                primary.certificate_chain = list(set([str(c) for c in (primary.certificate_chain + chains)]))
            elif chains:
                primary.certificate_chain = chains
            
            # Update last_verified to most recent
            latest_verified = duplicates.order_by('-last_verified').first()
            if latest_verified and latest_verified.last_verified:
                primary.last_verified = latest_verified.last_verified
            
            primary.save()
            
            # Delete duplicates
            duplicates.delete()
            
            serializer = CertificateSerializer(primary)
            return Response({
                'success': True,
                'message': f'Merged {len(duplicate_ids)} duplicate certificates',
                'certificate': serializer.data,
                'merged_count': len(duplicate_ids)
            }, status=status.HTTP_200_OK)
            
        except Certificate.DoesNotExist:
            return Response(
                {'error': 'Primary certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_csv(self, request):
        """
        Export certificates to CSV with optional filtering.
        
        Query parameters:
        - filter_type: all | expiring | high_risk | by_issuer | critical | custom
        - days_threshold: For 'expiring' filter (default 30)
        - risk_threshold: For 'high_risk' filter (default 60)
        - issuer: For 'by_issuer' filter
        - For 'custom' filter, all query params are treated as custom filters
        
        Returns CSV file download
        """
        from apps.certificates.services import CertificateExportService
        
        try:
            service = CertificateExportService()
            filter_type = request.query_params.get('filter_type', 'all').lower()
            
            if filter_type == 'all':
                filename, content = service.export_all_certificates()
            
            elif filter_type == 'expiring':
                days_threshold = int(request.query_params.get('days_threshold', 30))
                filename, content = service.export_expiring_certificates(days_threshold)
            
            elif filter_type == 'high_risk':
                risk_threshold = int(request.query_params.get('risk_threshold', 60))
                filename, content = service.export_high_risk_certificates(risk_threshold)
            
            elif filter_type == 'by_issuer':
                issuer = request.query_params.get('issuer')
                if not issuer:
                    return Response(
                        {'error': 'issuer parameter required for by_issuer filter'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                filename, content = service.export_by_issuer(issuer)
            
            elif filter_type == 'critical':
                filename, content = service.export_critical_alerts()
            
            elif filter_type == 'custom':
                # Build custom filters from query params
                filters = {}
                
                if domain_contains := request.query_params.get('domain_contains'):
                    filters['domain_contains'] = domain_contains
                if issuer := request.query_params.get('issuer'):
                    filters['issuer'] = issuer
                if risk_level := request.query_params.get('risk_level'):
                    filters['risk_level'] = risk_level
                if risk_score_min := request.query_params.get('risk_score_min'):
                    filters['risk_score_min'] = int(risk_score_min)
                if risk_score_max := request.query_params.get('risk_score_max'):
                    filters['risk_score_max'] = int(risk_score_max)
                if key_length_min := request.query_params.get('key_length_min'):
                    filters['key_length_min'] = int(key_length_min)
                if key_length_max := request.query_params.get('key_length_max'):
                    filters['key_length_max'] = int(key_length_max)
                if status_filter := request.query_params.get('status'):
                    filters['status'] = status_filter
                if source_type := request.query_params.get('source_type'):
                    filters['source_type'] = source_type
                
                filename, content = service.export_custom_filter(filters)
            
            else:
                return Response(
                    {'error': f'Unknown filter_type: {filter_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Log the export action
            try:
                AuditLoggingService.log_action(
                    user=request.user,
                    action='certificate_export',
                    description=f'Exported certificates with filter: {filter_type}',
                    details={'filter_type': filter_type},
                    request=request,
                )
            except Exception:
                pass  # Don't fail if logging fails
            
            # Return CSV as file download
            response = HttpResponse(content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        except ValueError as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Export failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_enabled", "last_status"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "last_scan_at", "updated_at"]
    ordering = ["name"]

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def enable(self, request, pk=None):
        domain = self.get_object()
        domain.is_enabled = True
        domain.save(update_fields=["is_enabled", "updated_at"])
        return Response({"success": True, "message": f"Domain {domain.name} enabled"})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def disable(self, request, pk=None):
        domain = self.get_object()
        domain.is_enabled = False
        domain.save(update_fields=["is_enabled", "updated_at"])
        return Response({"success": True, "message": f"Domain {domain.name} disabled"})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrSuperAdmin])
    def scan(self, request, pk=None):
        domain = self.get_object()
        timeout = request.data.get("timeout", 10)
        update_if_exists = request.data.get("update_if_exists", True)
        service = CertificateFetchService(timeout=timeout)
        result = service.scan_and_store(
            domain.name,
            update_if_exists=update_if_exists,
            user=request.user,
            request=request,
            domain_obj=domain,
        )
        if result["success"]:
            cert_data = CertificateSerializer(result["certificate"]).data
            return Response(
                {
                    "success": True,
                    "message": result["message"],
                    "status": result["status"],
                    "certificate": cert_data,
                },
                status=status.HTTP_201_CREATED if result["status"] == "created" else status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": result["message"],
                "error": result.get("error"),
                "error_type": result.get("error_type", "error"),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="history")
    def history(self, request, pk=None):
        domain = self.get_object()
        queryset = domain.scan_history.all()[:100]
        serializer = DomainScanHistorySerializer(queryset, many=True)
        return Response({"success": True, "count": len(serializer.data), "results": serializer.data})
