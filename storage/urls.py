from django.urls import path
from storage import views

urlpatterns = [
    path("", views.reservation_table, name="reservation_table"),
    path("reserve/<int:unit_id>/", views.make_reservation, name="make_reservation"),
]