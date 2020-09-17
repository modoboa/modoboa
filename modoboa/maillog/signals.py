"""Modoboa stats signals."""

import django.dispatch

get_graph_sets = django.dispatch.Signal(providing_args=["user"])
