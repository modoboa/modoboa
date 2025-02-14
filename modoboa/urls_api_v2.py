"""External API urls."""

from django.urls import include, path

from modoboa.core.extensions import exts_pool

app_name = "api"

urlpatterns = [
    path("", include("modoboa.core.api.v2.urls")),
    path("", include("modoboa.admin.api.v2.urls")),
    path("", include("modoboa.parameters.api.v2.urls")),
    path("", include("modoboa.imap_migration.api.v2.urls")),
    path("", include("modoboa.limits.api.v1.urls")),
    path("", include("modoboa.relaydomains.api.v1.urls")),
    path("", include("modoboa.dmarc.api.v2.urls")),
    path("", include("modoboa.dnstools.api.v2.urls")),
    path("", include("modoboa.maillog.api.v2.urls")),
    path("", include("modoboa.transport.api.v2.urls")),
    path("", include("modoboa.pdfcredentials.api.v2.urls")),
    path("", include("modoboa.postfix_autoreply.api.v2.urls")),
    path("", include("modoboa.sievefilters.api.v2.urls")),
    path("", include("modoboa.contacts.urls")),
    path("", include("modoboa.calendars.urls")),
]

urlpatterns += exts_pool.get_urls(category="api")
