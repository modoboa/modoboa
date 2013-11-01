# coding: utf-8
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool
from .models import RelayDomain, RelayDomainAlias, Service

extension_events = [
    "RelayDomainCreated",
    "RelayDomainDeleted",
    "RelayDomainAliasCreated",
    "RelayDomainAliasDeleted",
    "ExtraRelayDomainForm",
    "FillRelayDomainInstances"
]


def init_limits_dependant_features():
    """Populate limits tables.

    Update the pool of every defined user (to add new limits) and
    update the *Resellers* group with new permissions.
    """
    from modoboa.core.models import User
    from modoboa.extensions.limits import controls

    for u in User.objects.all():
        controls.create_pool(u)
    grp = Group.objects.get(name='Resellers')
    for model in [RelayDomain, RelayDomainAlias, Service]:
        ct = ContentType.objects.get_for_model(model)
        name = model.__name__.lower()
        for action in ['add', 'change', 'delete']:
            grp.permissions.add(
                Permission.objects.get(
                    content_type=ct, codename='%s_%s' % (action, name)
                )
            )
    grp.save()


def init_amavis_dependant_features():
    """Populate amavis database.

    We create records for *users* and *policy* tables for each defined
    relay domain or relay domain alias.
    """
    from modoboa.extensions.amavis.models import Users
    from modoboa.extensions.amavis.lib import (
        create_user_and_policy, create_user_and_use_policy
    )

    for rdom in RelayDomain.objects.all():
        try:
            Users.objects.get(email="@%s" % rdom.name)
        except Users.DoesNotExist:
            create_user_and_policy(rdom.name)
        for rdomalias in rdom.relaydomainalias_set.all():
            try:
                Users.objects.get(email='@%s' % rdomalias.name)
            except Users.DoesNotExist:
                create_user_and_use_policy(rdomalias.name, rdom.name)


class PostfixRelayDomains(ModoExtension):
    name = "postfix_relay_domains"
    label = "Postfix relay domains"
    version = "1.0"
    description = ugettext_lazy("Relay domains support for Postfix")

    def init(self):
        """Initialisation method.

        Only run once, when the extension is enabled. Populates the
        service table with default entries.
        """
        for service_name in ['relay', 'smtp']:
            Service.objects.get_or_create(name=service_name)
        if exts_pool.is_extension_enabled('limits'):
            init_limits_dependant_features()

    def load(self):
        from .app_settings import AdminParametersForm

        parameters.register(
            AdminParametersForm, ugettext_lazy("Relay domains")
        )
        events.declare(extension_events)
        from modoboa.extensions.postfix_relay_domains import general_callbacks
        if exts_pool.is_extension_enabled('limits'):
            import limits_callbacks
        if exts_pool.is_extension_enabled('amavis'):
            import amavis_callbacks

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(PostfixRelayDomains)
