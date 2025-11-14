from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.reservation_views import (
    StorageViewSet,
    StorageUnitViewSet,
    ReservationViewSet,
    PaymentViewSet,
)

router = DefaultRouter()
router.register(r"services", StorageViewSet, basename="service")
router.register(r"units", StorageUnitViewSet, basename="unit")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
