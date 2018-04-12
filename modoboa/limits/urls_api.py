# -*- coding: utf-8 -*-

"""Limits API urls."""

from __future__ import unicode_literals

from rest_framework import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"resources", viewsets.ResourcesViewSet, base_name="resources")

urlpatterns = router.urls
