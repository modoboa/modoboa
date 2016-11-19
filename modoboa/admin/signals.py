"""Modoboa admin signals."""

import django.dispatch

extra_admin_content = django.dispatch.Signal(
    providing_args=["user", "location", "currentpage"])
extra_domain_actions = django.dispatch.Signal(
    providing_args=["user", "domain"])
extra_domain_dashboard_widgets = django.dispatch.Signal(
    providing_args=["user", "domain"])
extra_domain_menu_entries = django.dispatch.Signal(
    providing_args=["user"])
extra_account_dashboard_widgets = django.dispatch.Signal(
    providing_args=["user", "account"])
use_external_recipients = django.dispatch.Signal(providing_args=["recipients"])
