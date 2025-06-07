"""Modoboa admin signals."""

import django.dispatch

extra_domain_filters = django.dispatch.Signal()
extra_domain_qset_filters = django.dispatch.Signal()  # Provides domfilter, extrafilters
import_object = django.dispatch.Signal()  # Provides objtype
use_external_recipients = django.dispatch.Signal()  # Provides recipients
extra_account_identities_actions = django.dispatch.Signal()  # Provides account
