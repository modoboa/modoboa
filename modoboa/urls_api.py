"""External API urls."""

from django.urls import include, path

from modoboa.core.extensions import exts_pool

app_name = "api"

urlpatterns = [
    path('', include("modoboa.core.urls_api")),
    path('', include("modoboa.admin.urls_api")),
    path('', include("modoboa.limits.urls_api")),
    path('', include("modoboa.relaydomains.urls_api")),
] + exts_pool.get_urls(category="api")
