"""Modoboa core signals."""

import django.dispatch

account_auto_created = django.dispatch.Signal()  # Provides user
account_exported = django.dispatch.Signal()  # Provides account
account_imported = django.dispatch.Signal()  # Provides user, account, row
account_deleted = django.dispatch.Signal()  # Provides user
account_role_changed = django.dispatch.Signal()  # Provides account, role
account_password_updated = django.dispatch.Signal()  # Provides account password created
allow_password_change = django.dispatch.Signal()  # Provides user
can_create_object = (
    django.dispatch.Signal()
)  # Provides context, klass, object_type, count, instance

extra_role_permissions = django.dispatch.Signal()  # Provides role
get_announcements = django.dispatch.Signal()  # Provides location
get_top_notifications = django.dispatch.Signal()  # Provides include_all
initial_data_loaded = django.dispatch.Signal()  # Provides extname
register_postfix_maps = django.dispatch.Signal()
user_can_set_role = django.dispatch.Signal()  # Provides user, role, account
user_login = django.dispatch.Signal()  # Provides user, password
user_logout = django.dispatch.Signal()
