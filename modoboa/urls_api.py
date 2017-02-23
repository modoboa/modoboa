"""External API urls."""

from django.conf.urls import include, url


urlpatterns = [
    url("", include("modoboa.admin.urls_api")),
]
