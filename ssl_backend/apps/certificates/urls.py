from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CertificateViewSet, DomainViewSet
from .adcs_views import ADCSSourceViewSet

router = DefaultRouter()
router.register(r'adcs-sources', ADCSSourceViewSet, basename='adcs-sources')
router.register(r'domains', DomainViewSet, basename='domains')
router.register(r'', CertificateViewSet, basename='certificates')

urlpatterns = [
    path('', include(router.urls)),
]
