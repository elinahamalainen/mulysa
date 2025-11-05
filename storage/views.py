from django.http import HttpResponse
from django.shortcuts import render
from .models.storage_unit import StorageUnit

"""def storage_home(request):
    return HttpResponse("Storage will be here.")"""

def reservation_table(request):
    return render(request, "storage/reservation_table.html", )