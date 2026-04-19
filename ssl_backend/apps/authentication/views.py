from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

from .models import UserLoginLog, UserRegistrationLog, UserAuditLog
from .serializers import (
    RegisterSerializer, UserSerializer, UserListSerializer, UserUpdateSerializer,
    UserLoginLogSerializer, UserRegistrationLogSerializer, UserAuditLogSerializer
)
from .permissions import IsSuperAdmin

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
        
        user = authenticate(username=username, password=password)
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if user is None:
            # Log failed login
            UserLoginLog.objects.create(
                user=User.objects.filter(username=username).first(),
                ip_address=ip_address,
                user_agent=user_agent,
                is_successful=False,
                failure_reason='Invalid credentials'
            )
            return Response({'success': False, 'error': 'Invalid credentials'}, status=401)
        
        # Log successful login
        login_log = UserLoginLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            is_successful=True
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
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
