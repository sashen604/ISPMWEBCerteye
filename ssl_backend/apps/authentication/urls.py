from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, LoginView, ProfileView, LogoutView,
    UserListView, UserDetailView, UserRoleUpdateView,
    UserLoginLogsView, UserRegistrationLogsView, UserAuditLogsView
)

urlpatterns = [
    # Auth endpoints
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('refresh', TokenRefreshView.as_view(), name='refresh'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('profile', ProfileView.as_view(), name='profile'),
    
    # User management (SuperAdmin only)
    path('users', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/role', UserRoleUpdateView.as_view(), name='user-role-update'),
    
    # Audit logs (SuperAdmin only)
    path('logs/login', UserLoginLogsView.as_view(), name='login-logs'),
    path('logs/registration', UserRegistrationLogsView.as_view(), name='registration-logs'),
    path('logs/audit', UserAuditLogsView.as_view(), name='audit-logs'),
]
