"""Relay domains urls."""

from __future__ import unicode_literals

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^scan_services/$', views.scan_for_services,
        name="service_scan"),
]
