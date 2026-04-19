from django.urls import path
from .views import RiskEngineView

urlpatterns = [
    path('', RiskEngineView.as_view(), name='risk-engine'),
]
