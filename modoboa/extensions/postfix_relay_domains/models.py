import reversion
from django.db import models
from django.db.models.manager import Manager
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.core.models import ObjectAccess
from modoboa.lib import events, parameters
from modoboa.lib.permissions import ungrant_access_to_object
from modoboa.extensions.admin.models import DatesAware


class RelayDomainManager(Manager):

    def get_for_admin(self, admin):
        """Return the relay domains belonging to this admin.

        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if admin.is_superuser:
            return self.get_query_set()
        return self.get_query_set().filter(owners__user=admin)


class ServiceManager(Manager):

    def load_from_master_cf(self):
        """Load services from the master.cf file.

        Parse the configuration file to update the service table. New
        entries are saved and outdated ones (ie. present in the
        database but not in the file) are removed.
        """
        with open(parameters.get_admin('MASTER_CF_PATH')) as fp:
            content = fp.read()
        services = []
        for line in content.split('\n'):
            if not line or line.startswith('#'):
                continue
            parts = line.strip().split()
            if len(parts) != 8:
                continue
            if parts[7] != 'smtp':
                continue
            srv, created = self.get_or_create(name=parts[0])
            services.append(parts[0])
        to_delete = []
        for service in self.all():
            if not service.name in services:
                to_delete.append(service.name)
        Service.objects.filter(name__in=to_delete()).delete()


class Service(models.Model):
    name = models.CharField(
        ugettext_lazy('name'), max_length=100, unique=True,
        help_text=ugettext_lazy('The service name')
    )

    objects = ServiceManager()

    def __str__(self):
        return self.name


class RelayDomain(DatesAware):
    """Relay domain.

    A relay domain differs from a usual domaine because its final
    destination is not reached yet. It must be accepted by the MTA but
    it will then be transfered to another one.
    """
    name = models.CharField(
        ugettext_lazy('name'), max_length=100, unique=True,
        help_text=ugettext_lazy('The domain name')
    )
    target_host = models.CharField(
        ugettext_lazy('target host'), max_length=255,
        help_text=ugettext_lazy('')
    )
    service = models.ForeignKey(Service, default='relay')
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy('Check to activate this domain')
    )
    verify_recipients = models.BooleanField(
        ugettext_lazy('verify recipients'),
        help_text=ugettext_lazy('')
    )

    owners = generic.GenericRelation(ObjectAccess)

    objects = RelayDomainManager()

    class Meta:
        ordering = ['name']

    @property
    def tags(self):
        return [
            {"name": "relaydomain", "label": _("Relay Domain"), "type": "dom"},
            {"name": self.service.name, "label": "%s:" % self.service.name, 
             "type": "srv", "color": "info"}
        ]

    def __str__(self):
        return self.name

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("RelayDomainCreated", creator, self)

    def save(self, *args, **kwargs):
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(RelayDomain, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def delete(self):
        events.raiseEvent("RelayDomainDeleted", self)
        ungrant_access_to_object(self)
        super(RelayDomain, self).delete()

reversion.register(RelayDomain)
