# coding: utf-8
"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.extensions.admin.models import Domain
from modoboa.lib import events, parameters
from . import general_callbacks
from .models import Transport, Alias


class PostfixAutoreply(ModoExtension):

    """
    Auto-reply (vacation) functionality using Postfix.

    """
    name = "postfix_autoreply"
    label = "Postfix autoreply"
    version = "1.0"
    description = ugettext_lazy(
        "Auto-reply (vacation) functionality using Postfix")

    def load(self):
        from modoboa.extensions.postfix_autoreply.app_settings import (
            ParametersForm
        )
        parameters.register(
            ParametersForm, ugettext_lazy("Automatic replies"))

    def load_initial_data(self):
        """Create records for existing domains."""
        for dom in Domain.objects.all():
            try:
                Transport.objects.get(domain="autoreply.%s" % dom.name)
            except Transport.DoesNotExist:
                general_callbacks.onDomainCreated(None, dom)
            else:
                continue

            for mb in dom.mailbox_set.all():
                try:
                    Alias.objects.get(full_address=mb.full_address)
                except Alias.DoesNotExist:
                    general_callbacks.onMailboxCreated(None, mb)

exts_pool.register_extension(PostfixAutoreply)


@events.observe("ExtraUprefsRoutes")
def extra_routes():
    from django.conf.urls import url

    return [
        url(r'^user/autoreply/$',
            'modoboa.extensions.postfix_autoreply.views.autoreply',
            name="autoreply")
    ]
