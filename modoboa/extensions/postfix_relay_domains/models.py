import reversion
from django.db import models
from django.db.models.manager import Manager
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.core.models import ObjectAccess
from modoboa.lib import parameters
from modoboa.lib.exceptions import BadRequest, NotFound
from modoboa.extensions.admin.models import AdminObject


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
        Service.objects.filter(name__in=to_delete).delete()


class Service(models.Model):
    """Postfix service.
    """
    name = models.CharField(
        ugettext_lazy('name'), max_length=100, unique=True,
        help_text=ugettext_lazy('The service name')
    )

    objects = ServiceManager()

    def __str__(self):
        return self.name


class RelayDomain(AdminObject):
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
        help_text=ugettext_lazy('Remote destination of this domain')
    )
    service = models.ForeignKey(Service, default='relay')
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy('Check to activate this domain')
    )
    verify_recipients = models.BooleanField(
        ugettext_lazy('verify recipients'),
        help_text=ugettext_lazy('Check for valid recipients')
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

    @property
    def aliases(self):
        return self.relaydomainalias_set

    def __str__(self):
        return self.name

    def to_csv(self, csvwriter):
        """Export this relay domain to CSV.

        :param csvwriter:
        """
        csvwriter.writerow(
            ["relaydomain", self.name, self.target_host, 
             self.service.name, self.enabled, self.verify_recipients]
        )
        for rdalias in self.relaydomainalias_set.all():
            rdalias.to_csv(csvwriter)

    def from_csv(self, user, row):
        """Import a relay domain from CSV.

        :param user: user importing the relay domain
        :param str row: relay domain definition
        """
        if len(row) != 6:
            raise BadRequest(_("Invalid line"))
        self.name = row[1].strip()
        self.target_host = row[2].strip()
        self.service, created = Service.objects.get_or_create(name=row[3].strip())
        self.enabled = (row[4].strip() == 'True')
        self.verify_recipients = (row[5].strip() == 'True')
        self.save(creator=user)

    def post_create(self, creator):
        """Post creation actions.

        :param ``User`` creator: user whos created this relay domain
        """
        super(RelayDomain, self).post_create(creator)
        for rdomalias in self.relaydomainalias_set.all():
            rdomalias.post_create(creator)

reversion.register(RelayDomain)


class RelayDomainAlias(AdminObject):
    """Relay domain alias.

    """
    name = models.CharField(
        ugettext_lazy("name"), max_length=100, unique=True,
        help_text=ugettext_lazy("The alias name")
    )
    target = models.ForeignKey(
        RelayDomain, verbose_name=ugettext_lazy('target'),
        help_text=ugettext_lazy("The relay domain this alias points to")
    )
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to activate this alias")
    )

    def __str__(self):
        return self.name

    def to_csv(self, csvwriter):
        """Export this relay domain alias to CSV.

        :param csvwriter:
        """
        csvwriter.writerow(
            ['relaydomainalias', self.name, self.target.name, self.enabled]
        )

    def from_csv(self, user, row):
        """Import a relay domain alias from CSV.

        :param user: user importing the relay domain alias
        :param str row: relay domain alias definition
        """
        if len(row) != 4:
            raise BadRequest(_("Invalid line"))
        self.name = row[1].strip()
        try:
            self.target = RelayDomain.objects.get(name=row[2].strip())
        except RelayDomain.DoesNotExist:
            raise NotFound(_("Relay domain %s does not exist" % row[2].strip()))
        self.enabled = (row[3].strip() == 'True')
        self.save(creator=user)

reversion.register(RelayDomainAlias)
