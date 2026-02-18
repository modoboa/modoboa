"""Modoboa rspamd handlers."""

from django.dispatch import receiver

import django_rq

from modoboa.admin import signals
from modoboa.rspamd import jobs


@receiver(signals.dkim_keys_created)
def update_rspamd_dkim_maps(sender, domains, **kwargs):
    """Update config maps."""
    queue = django_rq.get_queue("modoboa")
    queue.enqueue(jobs.update_rspamd_maps, [domain.id for domain in domains])
