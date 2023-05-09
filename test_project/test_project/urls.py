from __future__ import unicode_literals

from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r"", include("modoboa.urls")),
]
