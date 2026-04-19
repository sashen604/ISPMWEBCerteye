from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer, UserListSerializer, UserUpdateSerializer
from .permissions import IsSuperAdmin

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'success': True, 'user': UserSerializer(user).data}, status=201)


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
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'success': True, 'message': 'Logged out'})


class UserListView(APIView):
    """List all users - Admin/SuperAdmin only"""
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
        
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'user': UserSerializer(user).data})
    
    def delete(self, request, pk):
        """Delete a user - cannot delete yourself"""
        user = self.get_user_or_404(pk)
        if not user:
            return Response({'success': False, 'error': 'User not found'}, status=404)
        
        if user.id == request.user.id:
            return Response({'success': False, 'error': 'Cannot delete your own account'}, status=400)
        
        username = user.username
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
        
        return Response({
            'success': True,
            'message': f'User role updated from {old_role} to {new_role}',
            'user': UserSerializer(user).data
        })
