from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from apps.alerts.services import AlertEngine
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertSerializer

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
        
        alert_type = request.query_params.get('alert_type') or request.query_params.get('type')
        if alert_type:
            alerts = alerts.filter(alert_type__iexact=alert_type)

        is_acknowledged = request.query_params.get('is_acknowledged')
        if is_acknowledged is not None:
            alerts = alerts.filter(is_acknowledged=str(is_acknowledged).lower() in ['1', 'true', 'yes'])
        
        # Pagination
        limit = int(request.query_params.get('limit', 50))
        alerts = alerts[:limit]
        
        data = AlertSerializer(alerts, many=True).data
        
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
            if alert_type not in ['expiry', 'risk', 'both']:
                return Response(
                    {'error': f'Invalid alert_type: {alert_type}. Must be expiry, risk, or both.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize alert engine
            engine = AlertEngine(expiry_thresholds=custom_thresholds)
            
            all_alerts = []
            expiry_count = 0
            risk_count = 0
            
            # Generate expiry alerts
            if alert_type in ['expiry', 'both']:
                expiry_alerts = engine.generate_expiry_alerts()
                all_alerts.extend(expiry_alerts)
                expiry_count = len(expiry_alerts)
                logger.info(f"Generated {expiry_count} expiry alerts")
            
            # Generate risk alerts
            if alert_type in ['risk', 'both']:
                risk_alerts = engine.generate_immediate_risk_alerts()
                all_alerts.extend(risk_alerts)
                risk_count = len(risk_alerts)
                logger.info(f"Generated {risk_count} risk alerts")
            
            return Response({
                'success': True,
                'expiry_alerts': expiry_count,
                'risk_alerts': risk_count,
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
                    'alert': AlertSerializer(alert).data
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

    def patch(self, request, alert_id=None):
        """Acknowledge an alert."""
        if not alert_id:
            return Response({'error': 'alert_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(request.user, 'role') or request.user.role not in ['superadmin', 'admin']:
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            alert = Alert.objects.get(id=alert_id)
        except Alert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=status.HTTP_404_NOT_FOUND)

        is_acknowledged = request.data.get('is_acknowledged', True)
        alert.is_acknowledged = bool(is_acknowledged)
        if alert.is_acknowledged:
            alert.acknowledged_by = request.user.username
            alert.acknowledged_at = timezone.now()
        else:
            alert.acknowledged_by = None
            alert.acknowledged_at = None
        alert.save(update_fields=['is_acknowledged', 'acknowledged_by', 'acknowledged_at', 'updated_at'])
        return Response({'success': True, 'alert': AlertSerializer(alert).data})
