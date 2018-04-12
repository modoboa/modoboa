# -*- coding: utf-8 -*-

"""Custom urls."""

from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.test_view, name="index")
]
