from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import RiskConfiguration
from .serializers import RiskConfigurationSerializer
from apps.risk_engine.services import RiskScoringEngine

User = get_user_model()


def is_superadmin(user):
    """Check if user is superadmin."""
    return user.is_authenticated and hasattr(user, 'is_superadmin') and user.is_superadmin()


class RiskEngineView(APIView):
    """Legacy endpoint - kept for compatibility."""
    def get(self, request):
        return Response({'success': True, 'message': 'Risk engine endpoint'})


class RiskConfigurationView(APIView):
    """
    Manage risk scoring configuration (superadmin only).
    
    GET: View current risk thresholds
    PATCH: Update risk thresholds (superadmin only)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current risk configuration."""
        try:
            config = RiskConfiguration.objects.latest('last_modified_at')
        except RiskConfiguration.DoesNotExist:
            # Create default configuration if none exists
            config = RiskConfiguration.objects.create()
        
        serializer = RiskConfigurationSerializer(config)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def patch(self, request):
        """
        Update risk configuration (superadmin only).
        
        Only superadmins can modify risk thresholds to ensure
        risk scoring remains deterministic and audit-logged.
        """
        # Check superadmin permission
        if not is_superadmin(request.user):
            return Response({
                'success': False,
                'error': 'Only superadmins can modify risk configuration'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get current configuration
        try:
            config = RiskConfiguration.objects.latest('last_modified_at')
        except RiskConfiguration.DoesNotExist:
            config = RiskConfiguration.objects.create()
        
        # Update with new values
        serializer = RiskConfigurationSerializer(
            config,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save with current user as modifier
        instance = serializer.save(last_modified_by=request.user)
        
        # Log the change to audit trail (if audit logging is available)
        try:
            from apps.audit_logs.models import AuditLog
            AuditLog.objects.create(
                action='risk_config_update',
                actor=request.user,
                details={
                    'old_values': serializer.initial_data,
                    'new_values': RiskConfigurationSerializer(instance).data,
                    'ip_address': self._get_client_ip(request),
                }
            )
        except (ImportError, AttributeError):
            pass  # Audit logging not available
        
        return Response({
            'success': True,
            'message': 'Risk configuration updated successfully',
            'data': RiskConfigurationSerializer(instance).data
        })
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RiskAnalysisView(APIView):
    """
    Analyze risk for a specific certificate (for testing/debugging).
    
    POST: Calculate risk score for given certificate parameters
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Analyze risk for certificate parameters.
        
        Request body:
        {
            "valid_to": "2026-12-31T23:59:59Z",
            "key_length": 2048,
            "is_self_signed": false,
            "algorithm": "sha256WithRSAEncryption"
        }
        """
        try:
            # Extract parameters
            from dateutil.parser import parse as parse_datetime
            
            valid_to_str = request.data.get('valid_to')
            key_length = request.data.get('key_length')
            is_self_signed = request.data.get('is_self_signed', False)
            algorithm = request.data.get('algorithm')
            
            # Validate required fields
            if not valid_to_str or key_length is None:
                return Response({
                    'success': False,
                    'error': 'Missing required fields: valid_to, key_length'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse datetime
            valid_to = parse_datetime(valid_to_str)
            
            # Calculate risk
            risk_score = RiskScoringEngine.calculate_risk_score(
                valid_to=valid_to,
                key_length=key_length,
                is_self_signed=is_self_signed,
                algorithm=algorithm
            )
            risk_level = RiskScoringEngine.determine_risk_level(risk_score)
            reasoning = RiskScoringEngine.get_risk_reasoning(
                valid_to=valid_to,
                key_length=key_length,
                is_self_signed=is_self_signed,
                algorithm=algorithm
            )
            
            return Response({
                'success': True,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'reasoning': reasoning
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

