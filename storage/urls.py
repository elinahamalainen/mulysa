from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StorageViewSet,
    StorageUnitViewSet,
    ReservationViewSet,
    PaymentViewSet,
)

# Luo DefaultRouter
router = DefaultRouter()
router.register(r'services', StorageViewSet, basename='service')
router.register(r'units', StorageUnitViewSet, basename='unit')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'payments', PaymentViewSet, basename='payment')

# Routerin URLit
urlpatterns = [
    path('', include(router.urls)),
]