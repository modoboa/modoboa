# -*- coding: utf-8 -*-

"""Modoboa core signals."""

from __future__ import unicode_literals

import django.dispatch

account_auto_created = django.dispatch.Signal(providing_args=["user"])
account_exported = django.dispatch.Signal(providing_args=["account"])
account_imported = django.dispatch.Signal(
    providing_args=["user", "account", "row"])
account_deleted = django.dispatch.Signal(providing_args=["user"])
account_role_changed = django.dispatch.Signal(
    providing_args=["account", "role"])
account_password_updated = django.dispatch.Signal(
    providing_args=["account", "password", "created"])
allow_password_change = django.dispatch.Signal(providing_args=["user"])
can_create_object = django.dispatch.Signal(
    providing_args=["context", "klass", "object_type", "count", "instance"])
extra_account_actions = django.dispatch.Signal(providing_args=["account"])
extra_admin_dashboard_widgets = django.dispatch.Signal(
    providing_args=["user"])
extra_admin_menu_entries = django.dispatch.Signal(
    providing_args=["location", "user"])
extra_role_permissions = django.dispatch.Signal(providing_args=["role"])
extra_static_content = django.dispatch.Signal(
    providing_args=["caller", "st_type", "user"])
extra_uprefs_routes = django.dispatch.Signal()
extra_user_menu_entries = django.dispatch.Signal(
    providing_args=["location", "user"])
get_announcements = django.dispatch.Signal(providing_args=["location"])
get_top_notifications = django.dispatch.Signal(
    providing_args=["include_all"])
initial_data_loaded = django.dispatch.Signal(providing_args=["extname"])
register_postfix_maps = django.dispatch.Signal()
user_can_set_role = django.dispatch.Signal(
    providing_args=["user", "role", "account"])
user_login = django.dispatch.Signal(
    providing_args=["username", "password"])
user_logout = django.dispatch.Signal()
