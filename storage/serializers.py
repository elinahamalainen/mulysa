from rest_framework import serializers
from . import models


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
            "unit",          # käyttäjä antaa yksikön ID:n
            "start_date",
            "end_date",
        )


class StorageReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new reservation"""
    class Meta:
        model = models.StorageReservation
        fields = ("unit", "start_date", "end_date")


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
    reservation = serializers.PrimaryKeyRelatedField(
        queryset=models.StorageReservation.objects.all()
    )
    class Meta:
        model = models.StoragePayment
        fields = ("reservation", "amount", "months")

