"""
AD CS Views - REST API endpoints for AD CS management.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models_adcs import ADCSSource, ADCSSyncHistory, ADCSConnectionTest
from .adcs_serializers import (
    ADCSSourceSerializer,
    ADCSSyncHistorySerializer,
    ADCSConnectionTestSerializer
)
from .adcs_service import ADCSIntegrationService

logger = logging.getLogger(__name__)


class ADCSSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AD CS source management (CRUD operations).
    Only superadmin and admin users can manage AD CS sources.
    """
    
    queryset = ADCSSource.objects.all()
    serializer_class = ADCSSourceSerializer
    permission_classes = [IsAuthenticated]
    
    def _get_ip_address(self):
        """Extract IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def _check_permission(self):
        """Check if user has permission to manage AD CS sources."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        # Only superadmin and admin roles
        return user.is_superuser or getattr(user, 'role', None) == 'admin'
    
    def list(self, request, *args, **kwargs):
        """List all AD CS sources."""
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can view AD CS sources'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Register new AD CS source."""
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can register AD CS sources'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update AD CS source configuration."""
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can update AD CS sources'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete AD CS source."""
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can delete AD CS sources'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test connection to AD CS source.
        POST /api/adcs-sources/{id}/test_connection/
        """
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can test connections'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        source = get_object_or_404(ADCSSource, pk=pk)
        ip_address = self._get_ip_address()
        
        result = ADCSIntegrationService.test_connection(
            source,
            user=request.user,
            ip_address=ip_address
        )
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Synchronize certificates from AD CS source.
        POST /api/adcs-sources/{id}/sync/
        """
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can trigger sync'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        source = get_object_or_404(ADCSSource, pk=pk)
        ip_address = self._get_ip_address()
        
        result = ADCSIntegrationService.sync_certificates(
            source,
            user=request.user,
            ip_address=ip_address
        )
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def sync_history(self, request, pk=None):
        """
        Get sync history for AD CS source.
        GET /api/adcs-sources/{id}/sync_history/
        """
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can view sync history'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        source = get_object_or_404(ADCSSource, pk=pk)
        
        # Pagination
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        try:
            limit = int(limit)
            offset = int(offset)
        except ValueError:
            limit = 20
            offset = 0
        
        # Get sync history for this source
        history = ADCSSyncHistory.objects.filter(
            source=source
        ).order_by('-created_at')[offset:offset+limit]
        
        serializer = ADCSSyncHistorySerializer(history, many=True)
        
        return Response({
            'count': ADCSSyncHistory.objects.filter(source=source).count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def connection_tests(self, request, pk=None):
        """
        Get recent connection tests for AD CS source.
        GET /api/adcs-sources/{id}/connection_tests/
        """
        if not self._check_permission():
            return Response(
                {'detail': 'Only superadmin/admin can view connection tests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        source = get_object_or_404(ADCSSource, pk=pk)
        
        # Get recent connection tests
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        tests = ADCSConnectionTest.objects.filter(
            source=source
        ).order_by('-created_at')[:limit]
        
        serializer = ADCSConnectionTestSerializer(tests, many=True)
        
        return Response({
            'count': len(tests),
            'results': serializer.data
        })
