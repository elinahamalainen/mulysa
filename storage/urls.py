from django.urls import path
from storage import views

urlpatterns = [
    path("", views.reservation_table, name="reservation_table"),
]