"""Autoconfig urls."""

from django.urls import path

from modoboa.autoconfig import views

app_name = "autoconfig"

urlpatterns = [
    path(
        "mail/config-v1.1.xml",
        views.AutoConfigView.as_view(),
        name="autoconfig",
    ),
    path(
        "autodiscover/autodiscover.xml",
        views.AutoDiscoverView.as_view(),
        name="autodiscover",
    ),
    path("mobileconfig", views.MobileConfigView.as_view(), name="mobileconfig"),
]
