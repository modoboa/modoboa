import os
import reversion
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from modoboa.lib import parameters, events
from modoboa.lib.sysutils import exec_cmd
from modoboa.core.models import User
from modoboa.extensions.admin.exceptions import AdminError
from .base import DatesAware
from .domain import Domain


class Mailbox(DatesAware):
    address = models.CharField(
        ugettext_lazy('address'), max_length=252,
        help_text=ugettext_lazy("Mailbox address (without the @domain.tld part)")
    )
    quota = models.PositiveIntegerField()
    use_domain_quota = models.BooleanField(default=False)
    domain = models.ForeignKey(Domain)
    user = models.ForeignKey(User)

    class Meta:
        permissions = (
            ("view_mailboxes", "View mailboxes"),
        )

    def __init__(self, *args, **kwargs):
        super(Mailbox, self).__init__(*args, **kwargs)
        self.__mail_home = None

    def __str__(self):
        return self.full_address

    def __full_address(self, localpart):
        return "%s@%s" % (localpart, self.domain.name)

    @property
    def full_address(self):
        return self.__full_address(self.address)

    @property
    def enabled(self):
        return self.user.is_active

    @property
    def alias_count(self):
        return self.alias_set.count()

    @property
    def mail_home(self):
        """

        """
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return None
        if self.__mail_home is None:
            code, output = exec_cmd("doveadm user %s -f home" % self.full_address, 
                                    sudo_user=parameters.get_admin("MAILBOXES_OWNER"))
            if code:
                raise AdminError(_("Failed to retrieve mailbox location (%s)" % output))
            self.__mail_home = output.strip()
        return self.__mail_home

    def rename_dir(self, old_mail_home):
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return
        self.__mail_home = None
        if not os.path.exists(old_mail_home):
            return
        code, output = exec_cmd(
            "mv %s %s" % (old_mail_home, self.mail_home),
            sudo_user=parameters.get_admin("MAILBOXES_OWNER")
        )
        if code:
            raise AdminError(_("Failed to rename mailbox: %s" % output))

    def rename(self, address, domain):
        """Rename the mailbox

        :param string address: the new mailbox's address (local part)
        :param Domain domain: the new mailbox's domain
        """
        old_mail_home = self.mail_home
        qs = Quota.objects.filter(username=self.full_address)
        self.address = address
        self.domain = domain
        self.rename_dir(old_mail_home)
        qs.update(username=self.full_address)

    def delete_dir(self):
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return
        if not os.path.exists(self.mail_home):
            return
        code, output = exec_cmd(
            "rm -r %s" % self.mail_home,
            sudo_user=parameters.get_admin("MAILBOXES_OWNER")
        )
        if code:
            raise AdminError(_("Failed to remove mailbox: %s" % output))

    def set_quota(self, value=None, override_rules=False):
        """Set or update quota's value for this mailbox.

        :param integer value: the quota's value
        :param bool override_rules: allow to override defined quota rules
        """
        if value is None:
            if self.use_domain_quota:
                self.quota = self.domain.quota
            else:
                self.quota = 0
        elif int(value) > self.domain.quota and not override_rules:
            raise AdminError(
                _("Quota is greater than the allowed domain's limit (%dM)" % self.domain.quota)
            )
        else:
            self.quota = value
        if not self.quota and not override_rules:
            raise AdminError(_("A quota is required"))

    def get_quota(self):
        q = Quota.objects.get(username=self.full_address)
        return int(q.bytes / 1048576)

    def get_quota_in_percent(self):
        if not self.quota:
            return 0
        q = Quota.objects.get(username=self.full_address)
        return int(q.bytes / float(self.quota * 1048576) * 100)

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, True)
        events.raiseEvent("CreateMailbox", creator, self)
        if creator.is_superuser and not self.user.has_perm("admin.add_domain"):
            # A super user is creating a new mailbox. Give
            # access to that mailbox (and the associated
            # account) to the appropriate domain admins,
            # except if the new account has a more important
            # role (SuperAdmin, Reseller)
            for admin in self.domain.admins:
                grant_access_to_object(admin, self)
                grant_access_to_object(admin, self.user)

    def save(self, *args, **kwargs):
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(Mailbox, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)
        try:
            q = self.quota_value
        except Quota.DoesNotExist:
            Quota.objects.create(mbox=self, username=self.full_address)

    def delete(self, keepdir=False):
        """Custom delete method

        We try to delete the associated quota in the same time (it may
        has already been removed if we're deleting a domain).

        :param bool keepdir: delete the mailbox home dir on the filesystem or not
        """
        try:
            q = Quota.objects.get(username=self.full_address)
        except Quota.DoesNotExist:
            pass
        else:
            q.delete()
        if not keepdir:
            self.delete_dir()
        super(Mailbox, self).delete()

reversion.register(Mailbox)


@receiver(pre_delete, sender=Mailbox)
def mailbox_deleted_handler(sender, **kwargs):
    """``Mailbox`` pre_delete signal receiver

    In order to properly handle deletions (ie. we don't want to leave
    orphan records into the db), we define this custom receiver.

    It manually removes the mailbox from the aliases it is linked to
    and then remove all empty aliases.
    """
    from modoboa.lib.permissions import ungrant_access_to_object

    mb = kwargs['instance']
    events.raiseEvent("DeleteMailbox", mb)
    ungrant_access_to_object(mb)
    for alias in mb.alias_set.all():
        alias.mboxes.remove(mb)
        if alias.mboxes.count() == 0:
            alias.delete()


class Quota(models.Model):
    username = models.EmailField(primary_key=True, max_length=254)
    bytes = models.BigIntegerField(default=0)
    messages = models.IntegerField(default=0)

    mbox = models.OneToOneField(Mailbox, related_name="quota_value", null=True)
