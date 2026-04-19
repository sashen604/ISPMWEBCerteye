from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
import logging

from apps.alerts.services import AlertEngine
from apps.alerts.models import Alert

User = get_user_model()
logger = logging.getLogger(__name__)


class AlertsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all alerts (superadmin/admin only)."""
        # Check if user is admin
        if not hasattr(request.user, 'role') or request.user.role not in ['superadmin', 'admin']:
            return Response(
                {'error': 'Permission denied. Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alerts = Alert.objects.all().order_by('-created_at')
        
        # Optional filtering
        severity = request.query_params.get('severity')
        if severity:
            alerts = alerts.filter(severity__iexact=severity)
        
        alert_type = request.query_params.get('type')
        if alert_type:
            alerts = alerts.filter(title__icontains=alert_type)
        
        # Pagination
        limit = int(request.query_params.get('limit', 50))
        alerts = alerts[:limit]
        
        data = [{
            'id': alert.id,
            'title': alert.title,
            'severity': alert.severity,
            'message': alert.message,
            'created_at': alert.created_at.isoformat(),
        } for alert in alerts]
        
        return Response({'success': True, 'alerts': data, 'count': len(data)})


class AlertGeneratorView(APIView):
    """API for generating alerts based on certificate conditions."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate alerts for certificates.
        
        Request body:
        {
            "alert_type": "expiry" | "crypto_weakness" | "both",
            "custom_thresholds": {
                "CRITICAL": 7,
                "HIGH": 30,
                "MEDIUM": 90
            }  # Optional, custom thresholds for expiry alerts
        }
        
        Response:
        {
            "success": true,
            "expiry_alerts": N,
            "crypto_alerts": N,
            "total_alerts": N,
            "alerts": [ ... ]
        }
        """
        # Check if user is admin
        if not hasattr(request.user, 'role') or request.user.role not in ['superadmin', 'admin']:
            return Response(
                {'error': 'Permission denied. Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alert_type = request.data.get('alert_type', 'both').lower()
            custom_thresholds = request.data.get('custom_thresholds')
            
            # Validate alert_type
            if alert_type not in ['expiry', 'crypto_weakness', 'both']:
                return Response(
                    {'error': f'Invalid alert_type: {alert_type}. Must be expiry, crypto_weakness, or both.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize alert engine
            engine = AlertEngine(expiry_thresholds=custom_thresholds)
            
            all_alerts = []
            expiry_count = 0
            crypto_count = 0
            
            # Generate expiry alerts
            if alert_type in ['expiry', 'both']:
                expiry_alerts = engine.generate_expiry_alerts()
                all_alerts.extend(expiry_alerts)
                expiry_count = len(expiry_alerts)
                logger.info(f"Generated {expiry_count} expiry alerts")
            
            # Generate crypto weakness alerts
            if alert_type in ['crypto_weakness', 'both']:
                crypto_alerts = engine.generate_crypto_weakness_alerts()
                all_alerts.extend(crypto_alerts)
                crypto_count = len(crypto_alerts)
                logger.info(f"Generated {crypto_count} crypto weakness alerts")
            
            return Response({
                'success': True,
                'expiry_alerts': expiry_count,
                'crypto_alerts': crypto_count,
                'total_alerts': len(all_alerts),
                'alerts': all_alerts,
                'message': f'Generated {len(all_alerts)} alerts'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error generating alerts: {str(e)}")
            return Response(
                {'error': f'Failed to generate alerts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertDetailView(APIView):
    """Get alert details and statistics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, alert_id=None):
        """
        Get alert statistics or specific alert details.
        
        If alert_id provided: Get specific alert details
        If not: Get alert statistics
        """
        # Check if user is admin
        if not hasattr(request.user, 'role') or request.user.role not in ['superadmin', 'admin']:
            return Response(
                {'error': 'Permission denied. Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if alert_id:
            try:
                alert = Alert.objects.get(id=alert_id)
                return Response({
                    'success': True,
                    'alert': {
                        'id': alert.id,
                        'title': alert.title,
                        'severity': alert.severity,
                        'message': alert.message,
                        'created_at': alert.created_at.isoformat(),
                    }
                })
            except Alert.DoesNotExist:
                return Response(
                    {'error': 'Alert not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Return statistics
            all_alerts = Alert.objects.all()
            stats = {
                'total_alerts': all_alerts.count(),
                'critical_count': all_alerts.filter(severity__iexact='CRITICAL').count(),
                'high_count': all_alerts.filter(severity__iexact='HIGH').count(),
                'medium_count': all_alerts.filter(severity__iexact='MEDIUM').count(),
                'low_count': all_alerts.filter(severity__iexact='LOW').count(),
            }
            
            return Response({
                'success': True,
                'statistics': stats,
            })
