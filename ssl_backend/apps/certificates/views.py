from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Certificate
from .serializers import CertificateSerializer
from .services import CertificateFetchService


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
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
        
        # Scan and store certificate
        result = service.scan_and_store(domain, update_if_exists=update_if_exists)
        
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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
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
