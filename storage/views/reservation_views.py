from rest_framework import viewsets
from ..models import StorageService, StorageUnit, StorageReservation, StoragePayment
from ..serializers.reservation_serializers import (
    StorageSerializer,
    StorageUnitSerializer,
    StorageReservationSerializer,
    StorageReservationCreateSerializer,
    StoragePaymentSerializer,
    StoragePaymentCreateSerializer,
)
from django.utils import timezone
from datetime import timedelta
from utils import referencenumber


class StorageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Show all storages (read only)
    """

    queryset = StorageService.objects.all()
    serializer_class = StorageSerializer


class StorageUnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Show all storage units (read only)
    """

    queryset = StorageUnit.objects.all()
    serializer_class = StorageUnitSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Creates a new reservation for a storage unit.
    Sets automatically:
      - status = PENDING
      - reference_number = reference number
      - pending_until = the date the reservation has to be paid
    """

    queryset = StorageReservation.objects.select_related("unit").all()

    def get_serializer_class(self):
        if self.action == "create":
            return StorageReservationCreateSerializer
        return StorageReservationSerializer

    def perform_create(self, serializer):
        ref_number = str(referencenumber.generate_random(1000000, 9999999))

        reservation = serializer.save(
            user=self.request.user,
            status=StorageReservation.PENDING,
            reference_number=ref_number,
        )

        service = reservation.unit.service
        reservation.pending_until = timezone.now().date() + timedelta(
            days=service.pending_payment_days
        )

        reservation.max_duration_months = reservation.unit.max_rental_months
        reservation.save()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Creates a new payment for a reservation.
    Updates the reservation status as active and stores payment information.
    """

    queryset = StoragePayment.objects.select_related("reservation").all()

    def get_serializer_class(self):
        if self.action == "create":
            return StoragePaymentCreateSerializer
        return StoragePaymentSerializer

    def perform_create(self, serializer):
        reservation = serializer.validated_data["reservation"]

        # Create payment
        payment = serializer.save(
            reference_number=reservation.reference_number,
            paid_at=timezone.now(),
            verified=False,
        )

        # Update reservation status
        reservation.status = StorageReservation.ACTIVE
        reservation.paid_at = timezone.now()
        reservation.total_paid_months += payment.months
        reservation.save()
