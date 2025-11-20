from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models.storage_unit import StorageUnit
from .models.storage_reservation import StorageReservation
from storage.forms import StorageReservationForm
from datetime import date
from dateutil.relativedelta import relativedelta


@login_required
def reservation_table(request):
    units = StorageUnit.objects.all()
    reservations = StorageReservation.objects.filter(user=request.user)

    return render(request, "storage/reservation_table.html", {
        "units": units,
        "reservations": reservations
    })


@login_required
def make_reservation(request, unit_id):
    unit = get_object_or_404(StorageUnit, id=unit_id)

    if request.method == "POST":

        months = int(request.POST.get("months", 1))
        start = date.today()
        end = start + relativedelta(months=months)

        total_price = unit.price_per_month * months

        reservation = StorageReservation.objects.create(
            user=request.user,
            unit=unit,
            start_date = start,
            end_date = end,
            total_paid_months = 0,
            max_duration_months = months,
            status=StorageReservation.PENDING,
            paid_at=None
        )

        messages.success(request, "Reservation created successfully!")
        return redirect("reservation_table")

    return redirect("reservation_table")


