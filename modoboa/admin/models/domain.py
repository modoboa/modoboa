"""Models related to domains management."""

import datetime

from django.db import models
from django.db.models.manager import Manager
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _, ugettext_lazy

from django.contrib.contenttypes.fields import GenericRelation

from reversion import revisions as reversion

from modoboa.core.models import User, ObjectAccess
from modoboa.core import signals as core_signals
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import BadRequest, Conflict

from .base import AdminObject


class DomainManager(Manager):

    def get_for_admin(self, admin):
        """Return the domains belonging to this admin

        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if admin.is_superuser:
            return self.get_queryset()
        return self.get_queryset().filter(owners__user=admin)


@python_2_unicode_compatible
class Domain(AdminObject):
    """Mail domain."""

    name = models.CharField(ugettext_lazy('name'), max_length=100, unique=True,
                            help_text=ugettext_lazy("The domain name"))
    quota = models.IntegerField()
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to activate this domain"),
        default=True
    )
    owners = GenericRelation(ObjectAccess)
    type = models.CharField(default="domain", max_length=20)

    objects = DomainManager()

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
        )
        ordering = ["name"]
        app_label = "admin"

    def __init__(self, *args, **kwargs):
        """Save name for further use."""
        super(Domain, self).__init__(*args, **kwargs)
        self.old_mail_homes = None
        self.oldname = self.name

    @property
    def domainalias_count(self):
        return self.domainalias_set.count()

    @property
    def mailbox_count(self):
        return self.mailbox_set.count()

    @property
    def mbalias_count(self):
        return self.alias_set.count()

    @property
    def identities_count(self):
        """Total number of identities in this domain."""
        return (
            self.mailbox_set.count() +
            self.alias_set.filter(internal=False).count())

    @property
    def tags(self):
        if self.type == "domain":
            return [{"name": "domain", "label": _("Domain"), "type": "dom"}]
        return events.raiseQueryEvent("GetTagsForDomain", self)

    @property
    def admins(self):
        """Return the domain administrators of this domain.

        :return: a list of User objects
        """
        return User.objects.filter(
            is_superuser=False,
            objectaccess__content_type__model="domain",
            objectaccess__object_id=self.pk)

    @property
    def aliases(self):
        return self.domainalias_set

    @property
    def just_created(self):
        """return  true if the domain was created in the latest 24h"""
        now = timezone.now()
        delta = datetime.timedelta(days=1)
        return self.creation + delta > now

    def awaiting_checks(self):
        """return  true if the domain has no valid MX records and was created
        in the latest 24h"""
        if (not self.mxrecord_set.has_valids()) and self.just_created:
            return True
        return False

    @cached_property
    def dnsbl_status_color(self):
        """Shortcut to DNSBL results."""
        if not self.dnsblresult_set.exists():
            return "warning"
        elif self.dnsblresult_set.blacklisted().exists():
            return "danger"
        else:
            return "success"

    def add_admin(self, account):
        """Add a new administrator to this domain.

        :param User account: the administrator
        """
        from modoboa.lib.permissions import grant_access_to_object

        core_signals.can_create_object.send(
            sender=self.__class__, context=self, object_type="domain_admins")
        grant_access_to_object(account, self)
        for mb in self.mailbox_set.all():
            if mb.user.has_perm("admin.add_domain"):
                continue
            grant_access_to_object(account, mb)
            grant_access_to_object(account, mb.user)
        for al in self.alias_set.all():
            grant_access_to_object(account, al)

    def remove_admin(self, account):
        """Remove an administrator of this domain.

        :param User account: administrator to remove
        """
        from modoboa.lib.permissions import \
            ungrant_access_to_object, get_object_owner

        if get_object_owner(self) == account:
            events.raiseEvent('DomainOwnershipRemoved', account, self)
        ungrant_access_to_object(self, account)
        for mb in self.mailbox_set.all():
            if mb.user.has_perm("admin.add_domain"):
                continue
            ungrant_access_to_object(mb, account)
            ungrant_access_to_object(mb.user, account)
        for al in self.alias_set.all():
            ungrant_access_to_object(al, account)

    def save(self, *args, **kwargs):
        """Store current data if domain is renamed."""
        if self.oldname != self.name:
            self.old_mail_homes = (
                dict((mb.id, mb.mail_home) for mb in self.mailbox_set.all())
            )
        super(Domain, self).save(*args, **kwargs)

    def delete(self, fromuser, keepdir=False):
        """Custom delete method."""
        from modoboa.lib.permissions import ungrant_access_to_objects
        from .mailbox import Quota

        if self.domainalias_set.count():
            events.raiseEvent("DomainAliasDeleted", self.domainalias_set.all())
            ungrant_access_to_objects(self.domainalias_set.all())
        if self.alias_set.count():
            events.raiseEvent("MailboxAliasDeleted", self.alias_set.all())
            ungrant_access_to_objects(self.alias_set.all())
        if parameters.get_admin("AUTO_ACCOUNT_REMOVAL") == "yes":
            for account in User.objects.filter(mailbox__domain=self):
                account.delete(fromuser, keepdir)
        elif self.mailbox_set.count():
            Quota.objects.filter(username__contains='@%s' % self.name).delete()
            events.raiseEvent("MailboxDeleted", self.mailbox_set.all())
            ungrant_access_to_objects(self.mailbox_set.all())
        super(Domain, self).delete()

    def __str__(self):
        return smart_text(self.name)

    def from_csv(self, user, row):
        """Create a new domain from a CSV entry.

        The expected fields order is the following::

          "domain", name, quota, enabled

        :param ``core.User`` user: user creating the domain
        :param str row: a list containing domain's definition
        """
        if len(row) < 4:
            raise BadRequest(_("Invalid line"))
        self.name = row[1].strip()
        if Domain.objects.filter(name=self.name).exists():
            raise Conflict
        try:
            self.quota = int(row[2].strip())
        except ValueError:
            raise BadRequest(
                _("Invalid quota value for domain '%s'") % self.name)
        self.enabled = (row[3].strip() in ["True", "1", "yes", "y"])
        self.save(creator=user)

    def to_csv(self, csvwriter):
        csvwriter.writerow(["domain", self.name, self.quota, self.enabled])
        for dalias in self.domainalias_set.all():
            dalias.to_csv(csvwriter)

    def post_create(self, creator):
        """Post creation actions.

        :param ``User`` creator: user whos created this domain
        """
        super(Domain, self).post_create(creator)
        for domalias in self.domainalias_set.all():
            domalias.post_create(creator)

reversion.register(Domain)


class MXQuerySet(models.QuerySet):
    """Custom manager for MXRecord."""

    def has_valids(self):
        """Return managed results."""
        if parameters.get_admin("VALID_MXS", app="admin").strip():
            return self.filter(managed=True).exists()
        return self.exists()


class MXRecord(models.Model):
    """A model used to store MX records for Domain."""

    domain = models.ForeignKey(Domain)
    name = models.CharField(max_length=254)
    address = models.GenericIPAddressField()
    managed = models.BooleanField(default=False)
    updated = models.DateTimeField()

    objects = models.Manager.from_queryset(MXQuerySet)()

    def is_managed(self):
        if not parameters.get_admin("ENABLE_MX_CHECKS"):
            return False
        return bool(parameters.get_admin("VALID_MXS", app="admin").strip())

    def __unicode__(self):
        return u'{0.name} ({0.address}) for {0.domain} '.format(self)


class DNSBLQuerySet(models.QuerySet):
    """Custom manager for DNSBLResultManager."""

    def blacklisted(self):
        """Return blacklisted results."""
        return self.exclude(status="")


class DNSBLResult(models.Model):
    """Store a DNSBL query result."""

    domain = models.ForeignKey(Domain)
    provider = models.CharField(max_length=254, db_index=True)
    mx = models.ForeignKey(MXRecord)
    status = models.CharField(max_length=45, blank=True, db_index=True)

    objects = models.Manager.from_queryset(DNSBLQuerySet)()

    class Meta:
        app_label = "admin"
        unique_together = [("domain", "provider", "mx")]
