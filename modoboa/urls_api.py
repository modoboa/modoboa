"""External API urls."""

from django.conf.urls import include, url

from modoboa.core.extensions import exts_pool


urlpatterns = [
    url("", include("modoboa.admin.urls_api"))
]
urlpatterns += exts_pool.get_urls(category="api")
