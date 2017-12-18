from __future__ import unicode_literals

from django.conf.urls import include, url

urlpatterns = [
    url(r"", include("modoboa.urls")),
]
