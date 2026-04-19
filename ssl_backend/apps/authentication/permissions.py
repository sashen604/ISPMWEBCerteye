from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin())


class IsSuperAdmin(BasePermission):
    """Only SuperAdmin users can access"""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superadmin())


class IsAdminOrReadOnly(BasePermission):
    """Admin can modify, others read-only"""
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin())
