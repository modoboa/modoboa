# -*- coding: utf-8 -*-

"""External API urls."""

from __future__ import unicode_literals

from django.conf.urls import include, url

from modoboa.core.extensions import exts_pool

urlpatterns = [
    url("", include("modoboa.admin.urls_api")),
    url("", include("modoboa.limits.urls_api")),
    url("", include("modoboa.relaydomains.urls_api")),
]
urlpatterns += exts_pool.get_urls(category="api")
