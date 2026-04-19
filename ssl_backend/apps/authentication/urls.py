from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, LoginView, ProfileView, LogoutView,
    UserListView, UserDetailView, UserRoleUpdateView,
    UserLoginLogsView, UserRegistrationLogsView, UserAuditLogsView,
    # Security features
    SecuritySettingsView, ActiveSessionsView, IPWhitelistView,
    APIKeyView, APIKeyDetailView, SecurityAuditLogView,
    SuspiciousLoginAttemptsView, Enable2FAView, Disable2FAView
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
    
    # Security settings and features
    path('security/settings', SecuritySettingsView.as_view(), name='security-settings'),
    path('security/sessions', ActiveSessionsView.as_view(), name='active-sessions'),
    path('security/sessions/<int:pk>/', ActiveSessionsView.as_view(), name='session-detail'),
    path('security/ip-whitelist', IPWhitelistView.as_view(), name='ip-whitelist'),
    path('security/ip-whitelist/<int:pk>/', IPWhitelistView.as_view(), name='ip-whitelist-detail'),
    path('security/api-keys', APIKeyView.as_view(), name='api-keys'),
    path('security/api-keys/<int:pk>/', APIKeyDetailView.as_view(), name='api-key-detail'),
    path('security/audit-logs', SecurityAuditLogView.as_view(), name='security-audit-logs'),
    path('security/suspicious-attempts', SuspiciousLoginAttemptsView.as_view(), name='suspicious-attempts'),
    path('security/suspicious-attempts/<int:pk>/', SuspiciousLoginAttemptsView.as_view(), name='suspicious-attempt-detail'),
    path('security/2fa/enable', Enable2FAView.as_view(), name='enable-2fa'),
    path('security/2fa/disable', Disable2FAView.as_view(), name='disable-2fa'),
]
