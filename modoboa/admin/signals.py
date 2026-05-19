"""Modoboa admin signals."""

import django.dispatch

extra_domain_filters = django.dispatch.Signal()
extra_domain_qset_filters = django.dispatch.Signal()  # Provides domfilter, extrafilters
import_object = django.dispatch.Signal()  # Provides objtype
use_external_recipients = django.dispatch.Signal()  # Provides recipients
extra_account_identities_actions = django.dispatch.Signal()  # Provides account
dkim_keys_created = django.dispatch.Signal()  # Provides domains
# Receivers must return a dict of {field_name: serializer_field_instance}
extra_domain_serializer_fields = django.dispatch.Signal()
# Provides domain. Receivers must return a dict of {field_name: value}
# merged into the serialized representation (read side).
extra_domain_serializer_data = django.dispatch.Signal()
# Provides domain, plugin_data, request
domain_post_create_via_api = django.dispatch.Signal()
# Provides domain, plugin_data, request
domain_post_update_via_api = django.dispatch.Signal()
