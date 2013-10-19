import reversion
from django.db import models
from django.db.models.manager import Manager
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.contenttypes import generic
from modoboa.lib import events, parameters
from modoboa.core.models import User, ObjectAccess
from modoboa.extensions.admin.exceptions import AdminError
from .base import AdminObject


class DomainManager(Manager):

    def get_for_admin(self, admin):
        """Return the domains belonging to this admin

        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if admin.is_superuser:
            return self.get_query_set()
        return self.get_query_set().filter(owners__user=admin)


class Domain(AdminObject):
    name = models.CharField(ugettext_lazy('name'), max_length=100, unique=True,
                            help_text=ugettext_lazy("The domain name"))
    quota = models.IntegerField(
        help_text=ugettext_lazy("Default quota in MB applied to mailboxes")
    )
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to activate this domain")
    )
    owners = generic.GenericRelation(ObjectAccess)

    objects = DomainManager()

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
        )
        ordering = ["name"]
        app_label = 'admin'

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
    def tags(self):
        return [{"name": "domain", "label": _("Domain"), "type": "dom"}]

    @property
    def admins(self):
        """Return the domain administrators of this domain

        :return: a list of User objects
        """
        return [oa.user for oa in self.owners.filter(user__is_superuser=False)]

    def add_admin(self, account):
        """Add a new administrator for this domain

        :param User account: the administrotor to add
        """
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(account, self)
        for mb in self.mailbox_set.all():
            if mb.user.has_perm("admin.add_domain"):
                continue
            grant_access_to_object(account, mb)
            grant_access_to_object(account, mb.user)
        for al in self.alias_set.all():
            grant_access_to_object(account, al)

    def remove_admin(self, account):
        """Remove an administrator for this domain

        :param User account: the administrotor to remove
        """
        from modoboa.lib.permissions import ungrant_access_to_object
        ungrant_access_to_object(self, account)
        for mb in self.mailbox_set.all():
            if mb.user.has_perm("admin.add_domain"):
                continue
            ungrant_access_to_object(mb, account)
            ungrant_access_to_object(mb.user, account)
        for al in self.alias_set.all():
            ungrant_access_to_object(al, account)

    def delete(self, fromuser, keepdir=False):
        from modoboa.lib.permissions import \
            ungrant_access_to_object, ungrant_access_to_objects
        from .mailbox import Quota

        if self.domainalias_set.count():
            events.raiseEvent("DomainAliasDeleted", self.domainalias_set.all())
            ungrant_access_to_objects(self.domainalias_set.all())
        if self.mailbox_set.count():
            Quota.objects.filter(username__contains='@%s' % self.name).delete()
            events.raiseEvent("DeleteMailbox", self.mailbox_set.all())
            ungrant_access_to_objects(self.mailbox_set.all())
        if self.alias_set.count():
            events.raiseEvent("MailboxAliasDelete", self.alias_set.all())
            ungrant_access_to_objects(self.alias_set.all())
        if parameters.get_admin("AUTO_ACCOUNT_REMOVAL") == "yes":
            for account in User.objects.filter(mailbox__domain__name=self.name):
                account.delete(fromuser, keepdir)
        super(Domain, self).delete()

    def __str__(self):
        return self.name

    def from_csv(self, user, row):
        if len(row) < 4:
            raise AdminError(_("Invalid line"))
        self.name = row[1].strip()
        try:
            self.quota = int(row[2].strip())
        except ValueError:
            raise AdminError(_("Invalid quota value for domain '%s'" % self.name))
        self.enabled = (row[3].strip() == 'True')
        self.save(creator=user)

    def to_csv(self, csvwriter):
        csvwriter.writerow(["domain", self.name, self.quota, self.enabled])

reversion.register(Domain)
