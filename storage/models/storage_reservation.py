from django.db import models
from django.utils.translation import gettext_lazy as _
from storage.models.storage_unit import StorageUnit
from users.models.custom_user import CustomUser
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class StorageReservation(models.Model):
    """
    Represents a reservation of a storage unit by a user.
    Handles lifecycle states: pending (awaiting payment),
    active (paid), expired (unpaid past deadline), and completed.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    unit = models.ForeignKey(StorageUnit, on_delete=models.CASCADE)

    start_date = models.DateField(
        verbose_name=_("Start date"),
        help_text=_("The date when the reservation starts"),
    )

    end_date = models.DateField(
        verbose_name=_("End date"),
        help_text=_("The date when the reservation ends"),
    )

    # Reservation states
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    COMPLETED = "COMPLETED"

    RESERVATION_STATES = [
        (ACTIVE, _("Active")),
        (PENDING, _("Pending")),
        (EXPIRED, _("Expired")),
        (COMPLETED, _("Completed")),
    ]

    status = models.CharField(
        max_length=20,
        choices=RESERVATION_STATES,
        verbose_name=_("Status"),
        help_text=_("Current state of the reservation"),
    )

    total_paid_months = models.IntegerField(
        default=0,
        verbose_name=_("Total paid months"),
        help_text=_("How many months have been paid for this reservation."),
    )

    max_duration_months = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Maximum duration (months)"),
        help_text=_("Maximum allowed duration for this reservation."),
    )

    reference_number = models.CharField(
        blank=True,
        null=True,
        unique=True,
        max_length=25,
        verbose_name=_("Reference number"),
        help_text=_("Payment reference number for this reservation"),
    )

    pending_until = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Pending until"),
        help_text=_("Date when the pending reservation expires if unpaid."),
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Paid at"),
        help_text=_("Timestamp when the reservation was paid."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Automatically set when reservation is created"),
    )

    def __str__(self):
        return f"{self.unit} reserved by {self.user} ({self.status})"

    def is_active(self):
        """Return True if reservation is currently active."""
        today = timezone.now().date()
        return self.status == self.ACTIVE and self.start_date <= today <= self.end_date

    def mark_as_paid(self, months):
        """Activate reservation when payment is received."""
        self.status = self.ACTIVE
        self.paid_at = timezone.now()

        limit = self.max_duration_months or self.unit.max_rental_months
        current = self.total_paid_months or 0
        months_to_add = min(months, limit - current) if limit is not None else months
        self.total_paid_months = current + months_to_add

        self.end_date = self.start_date + relativedelta(months=self.total_paid_months)

        self.save(update_fields=["status", "paid_at", "total_paid_months", "end_date"])
        return months_to_add

    def expire_if_unpaid(self):
        """Expire reservation if payment deadline has passed."""
        today = timezone.now().date()
        if self.status == self.PENDING and today > self.pending_until:
            self.status = self.EXPIRED
            self.save(update_fields=["status"])
            return True
        return False

    def complete(self):
        """
        Mark reservation as completed.
        """
        today = timezone.now().date()
        if self.status == self.ACTIVE and self.end_date < today:
            self.status = self.COMPLETED
            self.save(update_fields=["status"])
            return True
        return False

    def extend(self, months):
        """
        Extend reservation duration by given number of months.
        Raises ValueError if the maximum duration would be exceeded.
        """
        if months < 1:
            raise ValueError("Extension duration must be at least one month.")

        limit = self.max_duration_months or self.unit.max_rental_months
        current = self.total_paid_months or 0

        # Calculate how many months can be addeds
        if limit is not None:
            remaining = max(limit - current, 0)
            if remaining == 0:
                raise ValueError("Reservation already at maximum duration.")
            months_to_add = min(months, remaining)
        else:
            months_to_add = months

        self.total_paid_months = current + months_to_add
        self.end_date = self.start_date + relativedelta(months=self.total_paid_months)

        self.save(update_fields=["end_date", "total_paid_months"])
        return months_to_add
