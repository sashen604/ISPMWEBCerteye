from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from datetime import datetime, timedelta

from .models import AuditLog, CertificateAuditLog, AlertAuditLog
from .serializers import AuditLogSerializer, CertificateAuditLogSerializer, AlertAuditLogSerializer


class IsSuperAdminOrAdmin(IsAuthenticated):
    """Permission class to allow only superadmin or admin users."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superadmin or request.user.is_admin


class AuditLogsView(APIView):
    """Main audit logs endpoint with filtering capabilities."""
    permission_classes = [IsSuperAdminOrAdmin]

    def get(self, request, log_id=None):
        """
        Get audit logs with optional filters.
        
        Query parameters:
        - action: Filter by action (login, certificate_create, etc.)
        - user_id: Filter by user ID
        - target_type: Filter by target type (certificate, alert, user)
        - date_from: Filter logs from date (YYYY-MM-DD)
        - date_to: Filter logs to date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - limit: Results per page (default: 50, max: 500)
        """
        
        # If requesting a specific log
        if log_id:
            try:
                log = AuditLog.objects.get(id=log_id)
                serializer = AuditLogSerializer(log)
                return Response({'success': True, 'data': serializer.data})
            except AuditLog.DoesNotExist:
                return Response(
                    {'error': 'Audit log not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get base queryset
        queryset = AuditLog.objects.select_related('user').all()
        
        # Apply filters
        action_filter = request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        user_id_filter = request.query_params.get('user_id')
        if user_id_filter:
            queryset = queryset.filter(user_id=user_id_filter)
        
        target_type_filter = request.query_params.get('target_type')
        if target_type_filter:
            queryset = queryset.filter(target_type=target_type_filter)
        
        # Date range filtering
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__gte=from_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(created_at__date__lt=to_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 500)  # Cap at 500
        
        start = (page - 1) * limit
        end = start + limit
        
        total_count = queryset.count()
        logs = queryset[start:end]
        
        serializer = AuditLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit,
            'data': serializer.data,
        })


class CertificateAuditLogsView(APIView):
    """Certificate-specific audit logs endpoint."""
    permission_classes = [IsSuperAdminOrAdmin]

    def get(self, request):
        """
        Get certificate audit logs with filters.
        
        Query parameters:
        - action: Filter by action (create, update, delete, scan)
        - certificate_id: Filter by certificate ID
        - user_id: Filter by user ID
        - date_from: Filter from date (YYYY-MM-DD)
        - date_to: Filter to date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - limit: Results per page (default: 50, max: 500)
        """
        
        queryset = CertificateAuditLog.objects.select_related('user').all()
        
        # Apply filters
        action_filter = request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        cert_id_filter = request.query_params.get('certificate_id')
        if cert_id_filter:
            queryset = queryset.filter(certificate_id=cert_id_filter)
        
        user_id_filter = request.query_params.get('user_id')
        if user_id_filter:
            queryset = queryset.filter(user_id=user_id_filter)
        
        # Date range filtering
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__date__gte=from_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__date__lt=to_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 500)
        
        start = (page - 1) * limit
        end = start + limit
        
        total_count = queryset.count()
        logs = queryset[start:end]
        
        serializer = CertificateAuditLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit,
            'data': serializer.data,
        })


class AlertAuditLogsView(APIView):
    """Alert-specific audit logs endpoint."""
    permission_classes = [IsSuperAdminOrAdmin]

    def get(self, request):
        """
        Get alert audit logs with filters.
        
        Query parameters:
        - action: Filter by action (create, update, resolve, reopen, dismiss)
        - alert_id: Filter by alert ID
        - certificate_id: Filter by certificate ID
        - user_id: Filter by user ID
        - date_from: Filter from date (YYYY-MM-DD)
        - date_to: Filter to date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - limit: Results per page (default: 50, max: 500)
        """
        
        queryset = AlertAuditLog.objects.select_related('user').all()
        
        # Apply filters
        action_filter = request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        alert_id_filter = request.query_params.get('alert_id')
        if alert_id_filter:
            queryset = queryset.filter(alert_id=alert_id_filter)
        
        cert_id_filter = request.query_params.get('certificate_id')
        if cert_id_filter:
            queryset = queryset.filter(certificate_id=cert_id_filter)
        
        user_id_filter = request.query_params.get('user_id')
        if user_id_filter:
            queryset = queryset.filter(user_id=user_id_filter)
        
        # Date range filtering
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__date__gte=from_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__date__lt=to_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 500)
        
        start = (page - 1) * limit
        end = start + limit
        
        total_count = queryset.count()
        logs = queryset[start:end]
        
        serializer = AlertAuditLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit,
            'data': serializer.data,
        })
