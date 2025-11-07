from rest_framework import serializers
from . import models
from django.utils import timezone


class StorageSerializer(serializers.ModelSerializer):
    """Basic information about storage service"""

    class Meta:
        model = models.StorageService
        fields = ("name", "description", "pending_payment_days", "created_at")


class StorageUnitSerializer(serializers.ModelSerializer):
    """Show storage unit information"""

    service = StorageSerializer()

    class Meta:
        model = models.StorageUnit
        fields = (
            "service",
            "name",
            "is_disabled",
            "price_per_month",
            "max_rental_months",
            "description",
            "show_name_publicly",
            "allow_self_subscription",
            "created_at",
        )


class StorageReservationSerializer(serializers.ModelSerializer):
    """Show reservation information (read only)"""

    unit = StorageUnitSerializer(read_only=True)

    class Meta:
        model = models.StorageReservation
        fields = (
            "unit",
            "start_date",
            "end_date",
            "status",
            "total_paid_months",
            "max_duration_months",
            "reference_number",
            "pending_until",
            "paid_at",
            "created_at",
        )
        read_only_fields = (
            "status",
            "reference_number",
            "pending_until",
            "paid_at",
            "created_at",
        )


class StorageReservationSerializer(serializers.ModelSerializer):
    """Used when creating a new reservation"""

    class Meta:
        model = models.StorageReservation
        fields = (
            "unit",
            "start_date",
            "end_date",
        )


class StorageReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new reservation

      Performs business rule validations:
    - Unit cannot already be reserved for the given period
    - Start date must be today
    - End date must be after start date
    - Reservation cannot exceed max_rental_months
    - Storage unit must be active (not disabled)
    - Storage service must allow self-subscription (if required)
    - User can only have one active/pending reservation at a time
    """

    class Meta:
        model = models.StorageReservation
        fields = ("unit", "start_date", "end_date")

    def validate(self, data):
        user = self.context["request"].user
        unit = data.get("unit")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not unit:
            raise serializers.ValidationError("Storage unit is required.")

        if not start_date or not end_date:
            raise serializers.ValidationError("Start and end dates are required.")

        if end_date < start_date:
            raise serializers.ValidationError("End date must be after start date.")

        today = timezone.now().date()
        if start_date != today:
            raise serializers.ValidationError("Reservation must start today.")

        if unit.is_disabled:
            raise serializers.ValidationError(
                "This storage unit is currently disabled."
            )

        if not unit.allow_self_subscription:
            raise serializers.ValidationError(
                "Self-subscription is not allowed for this storage unit."
            )

        duration_days = (end_date - start_date).days
        duration_months = duration_days / 30.0

        if unit.max_rental_months and duration_months > unit.max_rental_months:
            raise serializers.ValidationError(
                f"Reservation cannot exceed {unit.max_rental_months} months."
            )

        overlapping = models.StorageReservation.objects.filter(
            unit=unit,
            status__in=[
                models.StorageReservation.ACTIVE,
                models.StorageReservation.PENDING,
            ],
        ).filter(
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

        if overlapping.exists():
            raise serializers.ValidationError(
                f"Storage unit {unit.name} is already reserved or pending."
            )

        if not user.is_staff and not user.is_superuser:
            existing_reservation = models.StorageReservation.objects.filter(
                user=user,
                status__in=[
                    models.StorageReservation.ACTIVE,
                    models.StorageReservation.PENDING,
                ],
            )
            if existing_reservation.exists():
                raise serializers.ValidationError(
                    "You already have an active or pending reservation."
                )

        return data

    def create(self, validated_data):
        """Create reservation object (reference and payment handled in the view)."""
        return models.StorageReservation.objects.create(**validated_data)


class StoragePaymentSerializer(serializers.ModelSerializer):
    """Payment information and link to reservation"""

    reservation = serializers.PrimaryKeyRelatedField(
        queryset=models.StorageReservation.objects.all()
    )

    class Meta:
        model = models.StoragePayment
        fields = (
            "reservation",
            "reference_number",
            "amount",
            "months",
            "created_at",
            "paid_at",
        )
        read_only_fields = ("reference_number", "created_at", "paid_at")


class StoragePaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new payment

      Performs business rule validations:
    - User cannot pay for someone else's reservation
    - Reservation status must be pending or active
    - Payment months and amount must be greater than zero
    - Payment amount must match the monthly price of the unit and the amount of paid months
    - Paid months cannot exceed unit's maximum rental months
    """

    reservation = serializers.PrimaryKeyRelatedField(
        queryset=models.StorageReservation.objects.all()
    )

    class Meta:
        model = models.StoragePayment
        fields = ("reservation", "amount", "months")

    def validate(self, data):
        reservation = data.get("reservation")
        amount = data.get("amount")
        months = data.get("months")
        user = self.context["request"].user

        if not reservation:
            raise serializers.ValidationError("Reservation is required.")

        if reservation.user != user:
            raise serializers.ValidationError(
                "You cannot pay for someone else's reservation."
            )

        if reservation.status not in [
            models.StorageReservation.PENDING,
            models.StorageReservation.ACTIVE,
        ]:
            raise serializers.ValidationError(
                f"Cannot make payment for reservation in status {reservation.status}."
            )

        if months < 0:
            raise serializers.ValidationError("Paid months must be greater than zero.")

        if amount < 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        expected_amount = reservation.unit.price_per_month * months
        if amount != expected_amount:
            raise serializers.ValidationError(
                f"Incorrect payment amount. Expected {expected_amount:.2f} € for {months} month(s)."
            )

        if reservation.max_duration_months and (
            reservation.total_paid_months + months > reservation.max_duration_months
        ):
            raise serializers.ValidationError(
                f"Cannot pay for more than {reservation.max_duration_months} months total."
            )

        return data
