"""Custom urls."""

from django.urls import path

from . import views

app_name = "imap_migration"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
]
