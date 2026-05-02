from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

from .models import (
    UserLoginLog, UserRegistrationLog, UserAuditLog,
    UserSession, IPWhitelist, APIKey, SecurityAuditLog, SuspiciousLoginAttempt
)
from .serializers import (
    RegisterSerializer, UserSerializer, UserListSerializer, UserUpdateSerializer,
    UserLoginLogSerializer, UserRegistrationLogSerializer, UserAuditLogSerializer,
    UserSecuritySettingsSerializer, UserSessionSerializer, IPWhitelistSerializer,
    APIKeySerializer, APIKeyDetailSerializer, SecurityAuditLogSerializer,
    SuspiciousLoginAttemptSerializer
)
from .permissions import IsSuperAdmin
from apps.audit_logs.services import AuditLoggingService

User = get_user_model()


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=400)
        
        user = serializer.save()
        
        # Log registration
        UserRegistrationLog.objects.create(
            user=user,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            initial_role=user.role,
            registered_by=None
        )
        
        return Response({'success': True, 'user': UserSerializer(user).data}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        if not username or not password:
            UserLoginLog.objects.create(
                user=None,
                attempted_username=username or '',
                ip_address=ip_address,
                user_agent=user_agent,
                is_successful=False,
                failure_reason='Missing username or password',
            )
            return Response({'success': False, 'error': 'Invalid credentials'}, status=401)

        user = authenticate(username=username, password=password)

        if user is None:
            existing_user = User.objects.filter(username=username).first()
            UserLoginLog.objects.create(
                user=existing_user,
                attempted_username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_successful=False,
                failure_reason='Invalid credentials'
            )
            if existing_user:
                SecurityAuditLog.objects.create(
                    user=existing_user,
                    event_type='login_failed',
                    description='Failed login attempt',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status='failure',
                    metadata={'attempted_username': username, 'reason': 'invalid_credentials'},
                )
            AuditLoggingService.log_login(
                user=existing_user,
                success=False,
                failure_reason='Invalid credentials',
                request=request,
            )
            return Response({'success': False, 'error': 'Invalid credentials'}, status=401)

        # Log successful login
        UserLoginLog.objects.create(
            user=user,
            attempted_username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=True
        )
        SecurityAuditLog.objects.create(
            user=user,
            event_type='login_success',
            description='Successful login',
            ip_address=ip_address,
            user_agent=user_agent,
            status='success',
            metadata={'attempted_username': username},
        )
        AuditLoggingService.log_login(user=user, success=True, request=request)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({'success': True, 'user': UserSerializer(request.user).data})
    
    def put(self, request):
        """Allow users to update their own profile (email only)"""
        user = request.user
        email = request.data.get('email')
        if email:
            user.email = email
            user.save()
        return Response({'success': True, 'user': UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'success': False, 'error': 'Refresh token required'}, status=400)
        
        # Update the latest login log to record logout time
        latest_login = UserLoginLog.objects.filter(user=request.user, logout_time__isnull=True).order_by('-login_time').first()
        if latest_login:
            latest_login.logout_time = timezone.now()
            latest_login.session_duration = int((latest_login.logout_time - latest_login.login_time).total_seconds())
            latest_login.save()
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            pass

        AuditLoggingService.log_logout(user=request.user, request=request)
        
        return Response({'success': True, 'message': 'Logged out'})


class UserListView(APIView):
    """List all users - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        serializer = UserListSerializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'users': serializer.data
        })


class UserDetailView(APIView):
    """Get, update, or delete a specific user - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_user_or_404(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def get(self, request, pk):
        user = self.get_user_or_404(pk)
        if not user:
            return Response({'success': False, 'error': 'User not found'}, status=404)
        return Response({'success': True, 'user': UserSerializer(user).data})
    
    def patch(self, request, pk):
        """Update user role or status"""
        user = self.get_user_or_404(pk)
        if not user:
            return Response({'success': False, 'error': 'User not found'}, status=404)
        
        # Prevent self-demotion
        if user.id == request.user.id and request.data.get('role') and request.data.get('role') != User.ROLE_SUPERADMIN:
            return Response({'success': False, 'error': 'Cannot change your own role'}, status=400)
        
        old_role = user.role
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=400)
        
        serializer.save()
        
        # Log role change
        if old_role != user.role:
            UserAuditLog.objects.create(
                action='role_change',
                actor=request.user,
                target_user=user,
                old_value={'role': old_role},
                new_value={'role': user.role},
                ip_address=get_client_ip(request)
            )
        
        return Response({'success': True, 'user': UserSerializer(user).data})
    
    def delete(self, request, pk):
        """Delete a user - cannot delete yourself"""
        user = self.get_user_or_404(pk)
        if not user:
            return Response({'success': False, 'error': 'User not found'}, status=404)
        
        if user.id == request.user.id:
            return Response({'success': False, 'error': 'Cannot delete your own account'}, status=400)
        
        username = user.username
        
        # Log user deletion
        UserAuditLog.objects.create(
            action='user_deleted',
            actor=request.user,
            target_user=user,
            new_value={'deleted_user': username},
            ip_address=get_client_ip(request)
        )
        
        user.delete()
        return Response({'success': True, 'message': f'User {username} deleted'})


class UserRoleUpdateView(APIView):
    """Update a user's role - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'User not found'}, status=404)
        
        new_role = request.data.get('role')
        if not new_role:
            return Response({'success': False, 'error': 'Role is required'}, status=400)
        
        valid_roles = dict(User.ROLE_CHOICES)
        if new_role not in valid_roles:
            return Response({'success': False, 'error': f'Invalid role. Valid roles: {list(valid_roles.keys())}'}, status=400)
        
        old_role = user.role
        user.role = new_role
        user.save()
        
        # Log role change
        UserAuditLog.objects.create(
            action='role_change',
            actor=request.user,
            target_user=user,
            old_value={'role': old_role},
            new_value={'role': new_role},
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'message': f'User role updated from {old_role} to {new_role}',
            'user': UserSerializer(user).data
        })


class UserLoginLogsView(APIView):
    """View login logs for all users - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        
        if user_id:
            logs = UserLoginLog.objects.filter(user_id=user_id).order_by('-login_time')[:100]
        else:
            logs = UserLoginLog.objects.all().order_by('-login_time')[:500]
        
        serializer = UserLoginLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'count': len(logs),
            'logs': serializer.data
        })


class UserRegistrationLogsView(APIView):
    """View user registration logs - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        logs = UserRegistrationLog.objects.all().order_by('-registration_time')[:100]
        serializer = UserRegistrationLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'count': logs.count(),
            'logs': serializer.data
        })


class UserAuditLogsView(APIView):
    """View audit logs for user management actions - SuperAdmin only"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        target_user_id = request.query_params.get('target_user_id')
        
        if target_user_id:
            logs = UserAuditLog.objects.filter(target_user_id=target_user_id).order_by('-timestamp')[:100]
        else:
            logs = UserAuditLog.objects.all().order_by('-timestamp')[:200]
        
        serializer = UserAuditLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'count': len(logs),
            'logs': serializer.data
        })


# ============================================================================
# New Security Features Views
# ============================================================================

class SecuritySettingsView(APIView):
    """Get and update user security settings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current security settings"""
        serializer = UserSecuritySettingsSerializer(request.user)
        return Response({
            'success': True,
            'settings': serializer.data
        })
    
    def post(self, request):
        """Update security settings"""
        serializer = UserSecuritySettingsSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=400)
        
        serializer.save()
        
        # Log settings change
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type='settings_changed',
            description='User security settings updated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            metadata={'changes': request.data}
        )
        
        return Response({
            'success': True,
            'message': 'Security settings updated',
            'settings': serializer.data
        })


class ActiveSessionsView(APIView):
    """Get and manage active user sessions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all active sessions for current user"""
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response({
            'success': True,
            'sessions': serializer.data
        })
    
    def delete(self, request):
        """Sign out from all other sessions"""
        current_session_id = request.session.session_key if hasattr(request, 'session') else None
        
        # Deactivate all sessions except current
        UserSession.objects.filter(user=request.user).exclude(
            id=current_session_id
        ).update(is_active=False)
        
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type='session_terminated',
            description='All other sessions terminated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success'
        )
        
        return Response({
            'success': True,
            'message': 'Signed out from all other sessions'
        })


class IPWhitelistView(APIView):
    """Manage IP whitelist for user account"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get whitelisted IPs"""
        ips = IPWhitelist.objects.filter(user=request.user)
        serializer = IPWhitelistSerializer(ips, many=True)
        return Response({
            'success': True,
            'ips': serializer.data
        })
    
    def post(self, request):
        """Add IP to whitelist"""
        ip_address = request.data.get('ip_address')
        description = request.data.get('description', '')
        
        if not ip_address:
            return Response({'success': False, 'error': 'IP address required'}, status=400)
        
        ip_whitelist, created = IPWhitelist.objects.get_or_create(
            user=request.user,
            ip_address=ip_address,
            defaults={'description': description}
        )
        
        if created:
            SecurityAuditLog.objects.create(
                user=request.user,
                event_type='ip_whitelisted',
                description=f'IP {ip_address} whitelisted',
                ip_address=get_client_ip(request),
                status='success'
            )
        
        serializer = IPWhitelistSerializer(ip_whitelist)
        return Response({
            'success': True,
            'message': 'IP added to whitelist' if created else 'IP already whitelisted',
            'ip': serializer.data
        }, status=201 if created else 200)
    
    def delete(self, request, pk):
        """Remove IP from whitelist"""
        try:
            ip_whitelist = IPWhitelist.objects.get(pk=pk, user=request.user)
            ip_address = ip_whitelist.ip_address
            ip_whitelist.delete()
            
            SecurityAuditLog.objects.create(
                user=request.user,
                event_type='ip_whitelisted',
                description=f'IP {ip_address} removed from whitelist',
                ip_address=get_client_ip(request),
                status='success'
            )
            
            return Response({'success': True, 'message': 'IP removed from whitelist'})
        except IPWhitelist.DoesNotExist:
            return Response({'success': False, 'error': 'IP not found'}, status=404)


class APIKeyView(APIView):
    """Manage API keys for programmatic access"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all API keys for current user"""
        keys = APIKey.objects.filter(user=request.user)
        serializer = APIKeySerializer(keys, many=True)
        return Response({
            'success': True,
            'api_keys': serializer.data
        })
    
    def post(self, request):
        """Generate new API key"""
        name = request.data.get('name', f'API Key {timezone.now().strftime("%Y-%m-%d")}')
        
        key = APIKey.objects.create(
            user=request.user,
            name=name,
            key=APIKey.generate_key(),
            secret=APIKey.generate_secret(),
            expires_at=timezone.now() + timezone.timedelta(days=request.user.api_key_rotation_days)
        )
        
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type='api_key_created',
            description=f'API key "{name}" created',
            ip_address=get_client_ip(request),
            status='success'
        )
        
        serializer = APIKeyDetailSerializer(key)
        return Response({
            'success': True,
            'message': 'API key generated. Save it in a secure location!',
            'api_key': serializer.data
        }, status=201)


class APIKeyDetailView(APIView):
    """Delete/revoke an API key"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        """Revoke an API key"""
        try:
            api_key = APIKey.objects.get(pk=pk, user=request.user)
            name = api_key.name
            api_key.is_active = False
            api_key.save()
            
            SecurityAuditLog.objects.create(
                user=request.user,
                event_type='api_key_revoked',
                description=f'API key "{name}" revoked',
                ip_address=get_client_ip(request),
                status='success'
            )
            
            return Response({'success': True, 'message': 'API key revoked'})
        except APIKey.DoesNotExist:
            return Response({'success': False, 'error': 'API key not found'}, status=404)


class SecurityAuditLogView(APIView):
    """View security audit logs for current user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get security audit logs"""
        limit = int(request.query_params.get('limit', 50))
        logs = SecurityAuditLog.objects.filter(user=request.user).order_by('-timestamp')[:limit]
        serializer = SecurityAuditLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'count': len(logs),
            'logs': serializer.data
        })


class SuspiciousLoginAttemptsView(APIView):
    """View suspicious login attempts"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get suspicious login attempts"""
        attempts = SuspiciousLoginAttempt.objects.filter(
            user=request.user
        ).order_by('-timestamp')[:50]
        serializer = SuspiciousLoginAttemptSerializer(attempts, many=True)
        return Response({
            'success': True,
            'count': len(attempts),
            'attempts': serializer.data
        })
    
    def post(self, request, pk):
        """Mark suspicious attempt as verified (user's action)"""
        try:
            attempt = SuspiciousLoginAttempt.objects.get(pk=pk, user=request.user)
            attempt.is_verified = request.data.get('is_verified', False)
            attempt.save()
            
            if not attempt.is_verified:
                SecurityAuditLog.objects.create(
                    user=request.user,
                    event_type='login_suspicious',
                    description='User marked login attempt as unauthorized',
                    ip_address=get_client_ip(request),
                    status='warning'
                )
            
            serializer = SuspiciousLoginAttemptSerializer(attempt)
            return Response({'success': True, 'attempt': serializer.data})
        except SuspiciousLoginAttempt.DoesNotExist:
            return Response({'success': False, 'error': 'Attempt not found'}, status=404)


class Enable2FAView(APIView):
    """Enable 2FA for user account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate 2FA secret"""
        if request.user.enable_2fa:
            return Response({'success': False, 'error': '2FA already enabled'}, status=400)
        
        # For now, just prepare the 2FA settings
        # In production, integrate with qrcode and pyotp libraries
        secret_placeholder = f"2FA-SECRET-{request.user.id}-{timezone.now().timestamp()}"
        
        return Response({
            'success': True,
            'secret': secret_placeholder,
            'qr_code': f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/CertEye:{request.user.email}',
            'message': 'Scan this QR code with your authenticator app'
        })
    
    def put(self, request):
        """Verify and enable 2FA"""
        secret = request.data.get('secret')
        verification_code = request.data.get('verification_code')
        
        if not secret or not verification_code:
            return Response({'success': False, 'error': 'Secret and verification code required'}, status=400)
        
        # For now, accept any 6-digit code
        if not verification_code.isdigit() or len(verification_code) != 6:
            return Response({'success': False, 'error': 'Invalid verification code'}, status=400)
        
        request.user.two_fa_secret = secret
        # Generate backup codes
        import random
        backup_codes = [f"{random.randint(100000, 999999)}" for _ in range(10)]
        request.user.two_fa_backup_codes = backup_codes
        request.user.enable_2fa = True
        request.user.save()
        
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type='2fa_enabled',
            description='Two-factor authentication enabled',
            ip_address=get_client_ip(request),
            status='success'
        )
        
        return Response({
            'success': True,
            'message': '2FA enabled successfully',
            'backup_codes': backup_codes
        })


class Disable2FAView(APIView):
    """Disable 2FA for user account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Disable 2FA"""
        password = request.data.get('password')
        
        if not password:
            return Response({'success': False, 'error': 'Password required'}, status=400)
        
        if not request.user.check_password(password):
            return Response({'success': False, 'error': 'Invalid password'}, status=401)
        
        request.user.enable_2fa = False
        request.user.two_fa_secret = None
        request.user.two_fa_backup_codes = []
        request.user.save()
        
        SecurityAuditLog.objects.create(
            user=request.user,
            event_type='2fa_disabled',
            description='Two-factor authentication disabled',
            ip_address=get_client_ip(request),
            status='success'
        )
        
        return Response({
            'success': True,
            'message': '2FA disabled successfully'
        })
