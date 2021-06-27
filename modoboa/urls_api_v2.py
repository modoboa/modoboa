"""External API urls."""

from django.urls import include, path

from modoboa.core.extensions import exts_pool

app_name = "api"

urlpatterns = [
    path('', include("modoboa.core.api.v2.urls")),
    path('', include("modoboa.admin.api.v2.urls")),
    path('', include("modoboa.parameters.api.v2.urls")),
    path('', include("modoboa.limits.api.v1.urls")),
    path('', include("modoboa.relaydomains.api.v1.urls")),
    path('', include("modoboa.dnstools.api.v2.urls")),
    path('', include("modoboa.maillog.api.v2.urls")),
]

urlpatterns += exts_pool.get_urls(category="api")
