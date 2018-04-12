# -*- coding: utf-8 -*-

"""Limits API."""

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from rest_framework import mixins, viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

from modoboa.core import models as core_models
from . import serializers


class ResourcesViewSet(
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet):
    """Resources viewset."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = serializers.ResourcesSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = list(
            user.objectaccess_set.filter(
                content_type=ContentType.objects.get_for_model(user))
            .values_list("object_id", flat=True))
        if not user.is_superuser and user.pk in ids:
            ids.remove(user.pk)
        return core_models.User.objects.filter(pk__in=ids)
