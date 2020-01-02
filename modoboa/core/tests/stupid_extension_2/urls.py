"""Custom urls."""

from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.test_view, name="index")
]
