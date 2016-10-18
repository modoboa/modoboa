"""Modoboa core signals."""

import django.dispatch

can_create_object = django.dispatch.Signal(
    providing_args=["context", "object_type", "count"])
register_postfix_maps = django.dispatch.Signal()
