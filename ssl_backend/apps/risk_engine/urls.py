from django.urls import path
from .views import RiskEngineView, RiskConfigurationView, RiskAnalysisView

urlpatterns = [
    path('', RiskEngineView.as_view(), name='risk-engine'),
    path('config/', RiskConfigurationView.as_view(), name='risk-config'),
    path('analyze/', RiskAnalysisView.as_view(), name='risk-analyze'),
]
