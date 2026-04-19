# Audit Logging Service - Centralized logging for all audit events

from django.utils import timezone
from .models import AuditLog, CertificateAuditLog, AlertAuditLog


class AuditLoggingService:
    """Centralized service for audit logging across the application."""

    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request, handling proxies."""
        if request is None:
            return None
        
        # Check for forwarded IP (from proxy)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Fall back to direct IP
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def log_action(user, action, target_type='', target_id='', details=None, request=None):
        """
        Log a general action.
        
        Args:
            user: User object or None
            action: Action type (must match ACTION_CHOICES)
            target_type: Type of target (e.g., 'certificate', 'alert')
            target_id: ID of target
            details: Dictionary with additional context
            request: Optional HTTP request for IP extraction
        
        Returns:
            AuditLog instance
        """
        ip_address = AuditLoggingService.get_client_ip(request) if request else None
        
        audit_log = AuditLog.objects.create(
            user=user,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else '',
            details=details or {},
            ip_address=ip_address,
        )
        return audit_log

    @staticmethod
    def log_certificate_action(user, action, certificate_id=None, certificate_name='',
                               domain='', old_values=None, new_values=None, request=None):
        """
        Log a certificate operation.
        
        Args:
            user: User object or None
            action: Action type (create/update/delete/scan/import)
            certificate_id: Certificate ID
            certificate_name: Certificate name
            domain: Certificate domain
            old_values: Previous state (for updates/deletes)
            new_values: New state (for creates/updates)
            request: Optional HTTP request for IP extraction
        
        Returns:
            CertificateAuditLog instance
        """
        ip_address = AuditLoggingService.get_client_ip(request) if request else None
        
        cert_log = CertificateAuditLog.objects.create(
            user=user,
            action=action,
            certificate_id=certificate_id,
            certificate_name=certificate_name,
            domain=domain,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
        )
        return cert_log

    @staticmethod
    def log_alert_action(user, action, alert_id=None, alert_type='', certificate_id=None,
                         certificate_name='', old_values=None, new_values=None, request=None):
        """
        Log an alert operation.
        
        Args:
            user: User object or None
            action: Action type (create/update/resolve/reopen/dismiss)
            alert_id: Alert ID
            alert_type: Alert type/category
            certificate_id: Related certificate ID
            certificate_name: Related certificate name
            old_values: Previous state
            new_values: New state
            request: Optional HTTP request for IP extraction
        
        Returns:
            AlertAuditLog instance
        """
        ip_address = AuditLoggingService.get_client_ip(request) if request else None
        
        alert_log = AlertAuditLog.objects.create(
            user=user,
            action=action,
            alert_id=alert_id,
            alert_type=alert_type,
            certificate_id=certificate_id,
            certificate_name=certificate_name,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
        )
        return alert_log

    @staticmethod
    def log_login(user, success=True, failure_reason='', request=None):
        """Log user login event."""
        details = {'success': success}
        if failure_reason:
            details['failure_reason'] = failure_reason
        
        return AuditLoggingService.log_action(
            user=user,
            action='login',
            target_type='user',
            target_id=user.id if user else '',
            details=details,
            request=request,
        )

    @staticmethod
    def log_logout(user, request=None):
        """Log user logout event."""
        return AuditLoggingService.log_action(
            user=user,
            action='logout',
            target_type='user',
            target_id=user.id if user else '',
            request=request,
        )

    @staticmethod
    def log_role_change(user, target_user, old_role, new_role, request=None):
        """Log role change event."""
        return AuditLoggingService.log_action(
            user=user,
            action='role_change',
            target_type='user',
            target_id=target_user.id,
            details={
                'target_username': target_user.username,
                'old_role': old_role,
                'new_role': new_role,
            },
            request=request,
        )

    @staticmethod
    def log_risk_config_update(user, old_config, new_config, request=None):
        """Log risk configuration update."""
        return AuditLoggingService.log_action(
            user=user,
            action='risk_config_update',
            target_type='risk_configuration',
            details={
                'old_config': old_config,
                'new_config': new_config,
            },
            request=request,
        )

    @staticmethod
    def log_agent_submission(agent_id, status, ip_address=None, details=None):
        """Log agent submission event."""
        return AuditLoggingService.log_action(
            user=None,
            action='agent_submission',
            target_type='agent',
            target_id=agent_id,
            details=details or {'status': status},
            request=None,  # IP passed directly
        )
