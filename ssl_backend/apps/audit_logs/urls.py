from django.urls import path
from .views import AuditLogsView, CertificateAuditLogsView, AlertAuditLogsView

urlpatterns = [
    path('', AuditLogsView.as_view(), name='audit-logs'),
    path('certificates/', CertificateAuditLogsView.as_view(), name='certificate-audit-logs'),
    path('alerts/', AlertAuditLogsView.as_view(), name='alert-audit-logs'),
]
