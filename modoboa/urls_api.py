"""External API urls."""

from django.conf.urls import patterns, include


urlpatterns = patterns(
    "",

    ("", include("modoboa.admin.urls_api")),
)
