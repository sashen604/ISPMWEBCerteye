from django.urls import path
from .views import AlertsView, AlertGeneratorView, AlertDetailView

urlpatterns = [
    path('', AlertsView.as_view(), name='alerts'),
    path('generate/', AlertGeneratorView.as_view(), name='alert-generate'),
    path('stats/', AlertDetailView.as_view(), name='alert-stats'),
    path('<int:alert_id>/', AlertDetailView.as_view(), name='alert-detail'),
]
