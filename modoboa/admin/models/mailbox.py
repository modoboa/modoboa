"""Models related to mailboxes management."""

import os
import pwd

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.manager import Manager
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.translation import ugettext as _, ugettext_lazy

from reversion import revisions as reversion

from .base import AdminObject
from .domain import Domain
from modoboa.core.models import User
from modoboa.lib import events, parameters
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.sysutils import exec_cmd


class Quota(models.Model):

    """Keeps track of Mailbox current quota."""

    username = models.EmailField(primary_key=True, max_length=254)
    bytes = models.BigIntegerField(default=0)
    messages = models.IntegerField(default=0)

    class Meta:
        app_label = "admin"


class MailboxManager(Manager):

    """Custom manager for Mailbox."""

    def get_for_admin(self, admin, squery=None):
        """Return the mailboxes that belong to this admin.

        The result will contain the mailboxes defined for each domain that
        user can see.

        :param string squery: a search query
        :return: a list of ``Mailbox`` objects
        """
        qf = None
        if squery is not None:
            if '@' in squery:
                parts = squery.split('@')
                addrfilter = '@'.join(parts[:-1])
                domfilter = parts[-1]
                qf = (
                    Q(address__contains=addrfilter) &
                    Q(domain__name__contains=domfilter)
                )
            else:
                qf = (
                    Q(address__contains=squery) |
                    Q(domain__name__contains=squery)
                )
        ids = admin.objectaccess_set \
            .filter(content_type=ContentType.objects.get_for_model(Mailbox)) \
            .values_list('object_id', flat=True)
        if qf is not None:
            qf = Q(pk__in=ids) & qf
        else:
            qf = Q(pk__in=ids)
        return self.get_queryset().select_related().filter(qf)


@python_2_unicode_compatible
class Mailbox(AdminObject):

    """User mailbox."""

    address = models.CharField(
        ugettext_lazy('address'), max_length=252,
        help_text=ugettext_lazy(
            "Mailbox address (without the @domain.tld part)")
    )
    quota = models.PositiveIntegerField()
    use_domain_quota = models.BooleanField(default=False)
    domain = models.ForeignKey(Domain)
    user = models.OneToOneField(User)

    objects = MailboxManager()

    class Meta:
        permissions = (
            ("view_mailboxes", "View mailboxes"),
        )
        app_label = "admin"

    def __init__(self, *args, **kwargs):
        super(Mailbox, self).__init__(*args, **kwargs)
        self.__mail_home = None
        self.old_full_address = self.full_address

    def __str__(self):
        return smart_text(self.full_address)

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
        return (
            self.recipientalias_set.select_related("alias")
            .filter(alias__internal=False).count()
        )

    @property
    def mail_home(self):
        """Retrieve the home directory of this mailbox.

        The home directory refers to the place on the file system
        where the mailbox data is stored.

        We ask dovecot to give us this information because there are
        several patterns to understand and we don't want to implement
        them.
        """
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return None
        if self.__mail_home is None:
            curuser = pwd.getpwuid(os.getuid()).pw_name
            mbowner = parameters.get_admin("MAILBOXES_OWNER")
            options = {}
            if curuser != mbowner:
                options['sudo_user'] = mbowner
            code, output = exec_cmd(
                "doveadm user %s -f home" % self.full_address, **options
            )
            if code:
                raise lib_exceptions.InternalError(
                    _("Failed to retrieve mailbox location (%s)" % output))
            self.__mail_home = output.strip()
        return self.__mail_home

    @property
    def alias_addresses(self):
        """Return all alias address of this mailbox.

        :rtype: list of string
        """
        qset = (
            self.aliasrecipient_set.select_related("alias")
            .filter(alias__internal=False)
        )
        aliases = [alr.alias.address for alr in qset]
        return aliases

    @property
    def quota_value(self):
        """Retrieve the ``Quota`` instance associated to this mailbox."""
        if not hasattr(self, "_quota_value"):
            try:
                self._quota_value = Quota.objects.get(
                    username=self.full_address)
            except Quota.DoesNotExist:
                return None
        return self._quota_value

    @quota_value.setter
    def quota_value(self, instance):
        """Set the ``Quota`` for this mailbox."""
        self._quota_value = instance

    def rename_dir(self, old_mail_home):
        """Rename local directory if needed."""
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return
        MailboxOperation.objects.create(
            mailbox=self, type="rename", argument=old_mail_home
        )

    def rename(self, address, domain):
        """Rename the mailbox.

        To update the associated Quota record, we must create a new
        one first, update the foreign key and then we can delete the
        original record!

        :param string address: the new mailbox's address (local part)
        :param Domain domain: the new mailbox's domain

        """
        old_mail_home = self.mail_home
        old_qvalue = self.quota_value
        self.address = address
        self.domain = domain
        self.quota_value = Quota.objects.create(
            username=self.full_address, bytes=old_qvalue.bytes,
            messages=old_qvalue.messages
        )
        old_qvalue.delete()
        self.rename_dir(old_mail_home)

    def delete_dir(self):
        hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False)
        if hm is None or hm == "no":
            return
        MailboxOperation.objects.create(type='delete', argument=self.mail_home)

    def set_quota(self, value=None, override_rules=False):
        """Set or update quota's value for this mailbox.

        A value equal to 0 means the mailbox won't have any quota. The
        following cases allow people to define such behaviour:
        * The domain has no quota
        * :keyword:`override_rules` is True

        :param integer value: the quota's value
        :param bool override_rules: allow to override defined quota rules
        """
        if value is None:
            if self.use_domain_quota:
                self.quota = self.domain.quota
            else:
                self.quota = 0
        elif int(value) > self.domain.quota and not override_rules:
            raise lib_exceptions.BadRequest(
                _("Quota is greater than the allowed domain's limit (%dM)") %
                self.domain.quota
            )
        else:
            self.quota = value
        if not self.quota and self.domain.quota and not override_rules:
            raise lib_exceptions.BadRequest(_("A quota is required"))

    def get_quota(self):
        """Get quota limit.

        :rtype: int
        """
        return int(self.quota_value.bytes / 1048576)

    def get_quota_in_percent(self):
        """Get current quota usage.

        :rtype: int
        """
        if not self.quota:
            return 0
        return int(
            self.quota_value.bytes / float(self.quota * 1048576) * 100
        )

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        super(Mailbox, self).post_create(creator)
        conditions = (
            creator.has_perm("admin.add_mailbox"),
            not self.user.has_perm("admin.add_domain")
        )
        if all(conditions):
            # An admin is creating a new mailbox. Give
            # access to that mailbox (and the associated
            # account) to the appropriate domain admins,
            # except if the new account has a more important
            # role (SuperAdmin, Reseller)
            for admin in self.domain.admins:
                if admin == creator:
                    continue
                grant_access_to_object(admin, self)
                grant_access_to_object(admin, self.user)

    def update_from_dict(self, user, values):
        """Update mailbox from a dictionary."""
        newaddress = None
        if values["email"] != self.full_address:
            newaddress = values["email"]
        elif (self.user.role == "SimpleUsers" and
              self.user.username != self.full_address):
            newaddress = self.user.username
        if newaddress is not None:
            local_part, domname = split_mailbox(newaddress)
            domain = Domain.objects.filter(name=domname).first()
            if domain is None:
                raise lib_exceptions.NotFound(_("Domain does not exist"))
            if not user.can_access(domain):
                raise lib_exceptions.PermDeniedException
        if "use_domain_quota" in values:
            self.use_domain_quota = values["use_domain_quota"]
        override_rules = True \
            if not self.quota or user.has_perm("admin.add_domain") \
            else False
        self.set_quota(values["quota"], override_rules)
        if newaddress:
            self.rename(local_part, domain)
        self.save()
        events.raiseEvent("MailboxModified", self)

    def save(self, *args, **kwargs):
        """Custom save.

        We check that the address is unique and we make sure a quota
        record is defined for this mailbox.

        """
        qset = Mailbox.objects.filter(address=self.address, domain=self.domain)
        if self.pk:
            qset = qset.exclude(pk=self.pk)
        if qset.exists():
            raise lib_exceptions.Conflict(
                _("Mailbox {} already exists").format(self))
        if self.quota_value is None:
            self.quota_value, created = Quota.objects.get_or_create(
                username=self.full_address)
        super(Mailbox, self).save(*args, **kwargs)

    def delete(self, keepdir=False):
        """Custom delete method

        We try to delete the associated quota in the same time (it may
        has already been removed if we're deleting a domain).

        :param bool keepdir: delete the mailbox home dir on the
                             filesystem or not

        """
        Quota.objects.filter(username=self.full_address).delete()
        if not keepdir:
            self.delete_dir()
        super(Mailbox, self).delete()

reversion.register(Mailbox)


@python_2_unicode_compatible
class SenderAddress(models.Model):
    """Extra sender address for Mailbox."""

    address = models.EmailField()
    mailbox = models.ForeignKey(Mailbox)

    class Meta:
        app_label = "admin"
        unique_together = [
            ("address", "mailbox"),
        ]

    def __str__(self):
        """Return address."""
        return smart_text(self.address)

reversion.register(SenderAddress)


class MailboxOperation(models.Model):

    """An operation on a mailbox."""

    mailbox = models.ForeignKey(Mailbox, blank=True, null=True)
    type = models.CharField(
        max_length=20, choices=(('rename', 'rename'), ('delete', 'delete'))
    )
    argument = models.TextField()

    class Meta:
        app_label = "admin"

    def __str__(self):
        if self.type == 'rename':
            return 'Rename %s -> %s' % (self.argument, self.mailbox.mail_home)
        return 'Delete %s' % self.argument
