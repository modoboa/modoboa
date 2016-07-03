"""Modoboa admin signals."""

import django.dispatch

use_external_recipients = django.dispatch.Signal(providing_args=["recipients"])
extra_domain_actions = django.dispatch.Signal(
    providing_args=["user", "domain"])
extra_domain_dashboard_widgets = django.dispatch.Signal(
    providing_args=["user", "domain"])
extra_account_dashboard_widgets = django.dispatch.Signal(
    providing_args=["user", "account"])
