"""Relay domain related models."""

from django.db import models
from django.db.models.manager import Manager
from django.utils.translation import ugettext as _, ugettext_lazy

from reversion import revisions as reversion

from modoboa.admin import models as admin_models
from modoboa.lib.exceptions import BadRequest
from modoboa.parameters import tools as param_tools


class ServiceManager(Manager):

    def load_from_master_cf(self):
        """Load services from the master.cf file.

        Parse the configuration file to update the service table. New
        entries are saved and outdated ones (ie. present in the
        database but not in the file) are removed.
        """
        with open(param_tools.get_global_parameter("master_cf_path")) as fp:
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
            if service.name not in services:
                to_delete.append(service.name)
        Service.objects.filter(name__in=to_delete).delete()


class Service(models.Model):
    """Postfix service."""

    name = models.CharField(
        ugettext_lazy('name'), max_length=100, unique=True,
        help_text=ugettext_lazy('The service name')
    )

    objects = ServiceManager()

    class Meta:
        db_table = "postfix_relay_domains_service"

    def __str__(self):
        return self.name


class RelayDomain(admin_models.AdminObject):
    """Relay domain.

    A relay domain differs from a usual domaine because its final
    destination is not reached yet. It must be accepted by the MTA but
    it will then be transfered to another one.
    """

    domain = models.OneToOneField("admin.Domain", null=True)
    target_host = models.CharField(
        ugettext_lazy("target host address"), max_length=255,
        help_text=ugettext_lazy(
            "Remote address (hostname or IP) of this domain")
    )
    target_port = models.IntegerField(
        ugettext_lazy("target host port"),
        help_text=ugettext_lazy(
            "Remote port of this domain"),
        default=25
    )
    service = models.ForeignKey(Service)
    verify_recipients = models.BooleanField(
        ugettext_lazy('verify recipients'),
        help_text=ugettext_lazy('Check for valid recipients'),
        default=False
    )

    class Meta:
        ordering = ["domain__name"]
        db_table = "postfix_relay_domains_relaydomain"

    @property
    def tags(self):
        return [
            {"name": "relaydomain", "label": _("Relay Domain"), "type": "dom"},
            {"name": self.service.name, "label": "%s:" % self.service.name,
             "type": "srv", "color": "info"}
        ]

    def __str__(self):
        return self.domain.name

    def to_csv(self, csvwriter):
        """Export this relay domain to CSV.

        :param csvwriter:
        """
        csvwriter.writerow(
            ["relaydomain", self.domain.name, self.target_host,
             self.target_port, self.service.name, self.domain.enabled,
             self.verify_recipients]
        )
        for dalias in self.domain.domainalias_set.all():
            dalias.to_csv(csvwriter)

    def from_csv(self, user, row):
        """Import a relay domain from CSV.

        :param user: user importing the relay domain
        :param str row: relay domain definition
        """
        if len(row) != 7:
            raise BadRequest(_("Invalid line"))
        self.domain = admin_models.Domain(
            name=row[1].strip(), type="relaydomain", quota=0,
            enabled=(row[5].strip() in ["True", "1", "yes", "y"])
        )
        self.domain.save(creator=user)
        self.target_host = row[2].strip()
        self.target_port = row[3].strip()
        self.service, created = Service.objects.get_or_create(
            name=row[4].strip())
        self.verify_recipients = (row[6].strip() in ["True", "1", "yes", "y"])
        self.save(creator=user)


reversion.register(RelayDomain)
