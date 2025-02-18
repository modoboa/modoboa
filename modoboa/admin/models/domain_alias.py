"""Models related to domain aliases management."""

from reversion import revisions as reversion

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib.exceptions import BadRequest, Conflict
from .base import AdminObject
from .domain import Domain


class DomainAliasManager(models.Manager):

    def get_for_admin(self, admin):
        """Return the domain aliases belonging to this admin.

        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if admin.is_superuser:
            return self.get_queryset()
        return self.get_queryset().filter(owners__user=admin)


class DomainAlias(AdminObject):
    """Domain aliases."""

    name = models.CharField(
        gettext_lazy("name"),
        max_length=100,
        unique=True,
        help_text=gettext_lazy("The alias name"),
    )
    target = models.ForeignKey(
        Domain,
        verbose_name=gettext_lazy("target"),
        help_text=gettext_lazy("The domain this alias points to"),
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(
        gettext_lazy("enabled"),
        help_text=gettext_lazy("Check to activate this alias"),
        default=True,
    )

    owners = GenericRelation(core_models.ObjectAccess)

    objects = DomainAliasManager()

    class Meta:
        app_label = "admin"

    def __str__(self):
        return smart_str(self.name)

    def from_csv(self, user, row):
        """Create a domain alias from a CSV row

        Expected format: ["domainalias", domain alias name, targeted domain,
                          enabled]

        :param user: a ``User`` object
        :param row: a list containing the alias definition
        """
        if len(row) < 4:
            raise BadRequest(_("Invalid line"))
        self.name = row[1].strip().lower()
        for model in [DomainAlias, Domain]:
            if model.objects.filter(name=self.name).exists():
                raise Conflict
        domname = row[2].strip()
        try:
            self.target = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise BadRequest(_("Unknown domain %s") % domname) from None
        core_signals.can_create_object.send(
            sender="import", context=self.target, object_type="domain_aliases"
        )
        self.enabled = row[3].strip().lower() in ["true", "1", "yes", "y"]
        self.save(creator=user)

    def to_csv_row(self):
        """Export to row that can be included in a CSV file."""
        return ["domainalias", self.name, self.target.name, self.enabled]

    def to_csv(self, csvwriter):
        """Export a domain alias using CSV format

        :param csvwriter: a ``csv.writer`` object
        """
        csvwriter.writerow(self.to_csv_row())


reversion.register(DomainAlias)
