"""External API urls."""

from django.urls import include, path

from modoboa.core.extensions import exts_pool

app_name = "api"

urlpatterns = [
    path('', include("modoboa.core.api.v1.urls")),
    path('', include("modoboa.admin.api.v1.urls")),
    path('', include("modoboa.limits.urls_api")),
    path('', include("modoboa.relaydomains.urls_api"))
]

urlpatterns += exts_pool.get_urls(category="api")
