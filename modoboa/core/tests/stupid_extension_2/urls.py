"""Custom urls."""

from django.urls import re_path

from . import views

urlpatterns = [re_path("^$", views.test_view, name="index")]
