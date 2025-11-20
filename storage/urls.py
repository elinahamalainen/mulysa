from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.reservation_views import (
    StorageViewSet,
    StorageUnitViewSet,
    ReservationViewSet,
    PaymentViewSet,
)
from .views.admin_views import StorageAdminViewSet
from storage import views

router = DefaultRouter()
router.register(r"services", StorageViewSet, basename="service")
router.register(r"units", StorageUnitViewSet, basename="unit")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"admin/storage", StorageAdminViewSet, basename="storage-admin")

urlpatterns = [
    path("", include(router.urls)),
    path("", views.reservation_table, name="reservation_table"),
    path("reserve/<int:unit_id>/", views.make_reservation, name="make_reservation"),
]

