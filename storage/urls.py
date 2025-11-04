from django.urls import path
from storage import views

urlpatterns = [
    path("", views.storage_home, name="storage_home"),
]