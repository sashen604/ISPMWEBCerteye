from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/certificates/', include('apps.certificates.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/risk/', include('apps.risk_engine.urls')),
    path('api/audit/', include('apps.audit_logs.urls')),
]
