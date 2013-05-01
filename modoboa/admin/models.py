# coding: utf-8
from django.db import models, IntegrityError
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User as DUser, UserManager, Group
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.crypto import constant_time_compare
from django.conf import settings
from modoboa.lib import md5crypt, parameters, events
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.sysutils import exec_cmd, exec_as_vuser
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions import exts_pool
from exceptions import AdminError
import os
import sys
import pwd
import re
import crypt, hashlib, string, base64
from random import Random

try:
    from modoboa.lib.ldaputils import *
    ldap_available = True
except ImportError:
    ldap_available = False


class User(DUser):
    """Proxy for the ``User`` model.

    It overloads the way passwords are stored into the database. The
    main reason to change this mechanism is to ensure the
    compatibility with the way Dovecot stores passwords.

    It also adds new attributes and methods.
    """
    class Meta:
        proxy = True
        ordering = ["username"]

    password_expr = re.compile(r'(\{(\w+)\}|(\$1\$))(.+)')

    def __init__(self, *args, **kwargs):
        """Constructor

        A little hack to increase the maximum length for the username
        field.
        """
        max_length = 254
        DUser._meta.get_field('username').max_length = max_length
        DUser._meta.get_field('username').validators[0].limit_value = 254
        super(User, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.fullname

    def delete(self, fromuser, keep_mb_dir, *args, **kwargs):
        """Custom delete method

        To check permissions properly, we need to make a distinction
        between 2 cases:

        * If the user owns a mailbox, the check is made on that object
          (useful for domain admins)

        * Otherwise, the check is made on the user
        """
        from modoboa.lib.permissions import \
            get_object_owner, grant_access_to_object, ungrant_access_to_object

        if fromuser == self:
            raise AdminError(_("You can't delete your own account"))

        if not fromuser.can_access(self):
            raise PermDeniedException

        if self.has_mailbox:
            mb = self.mailbox_set.all()[0]
            if not fromuser.can_access(mb):
                raise PermDeniedException
            mb.delete(keepdir=keep_mb_dir)

        owner = get_object_owner(self)
        for ooentry in self.objectaccess_set.filter(is_owner=True):
            if ooentry.content_object is not None:
                grant_access_to_object(owner, ooentry.content_object, True)

        events.raiseEvent("AccountDeleted", self)
        ungrant_access_to_object(self)
        super(User, self).delete(*args, **kwargs)

    @staticmethod
    def get_content_type():
        """An uggly hack to retrieve the appropriate content_type!

        The explanation is available here:
        https://code.djangoproject.com/ticket/11154

        Quickly, the content_types framework does not retrieve the
        appropriate content type for proxy models, it retrieves the
        one of the first parent that is not a proxy.
        """
        if not hasattr(User, "ct"):
            User.ct = ContentType.objects.get(app_label="admin", model="user")
        return User.ct

    def _crypt_password(self, raw_value):
        scheme = parameters.get_admin("PASSWORD_SCHEME")
        if type(raw_value) is unicode:
            raw_value = raw_value.encode("utf-8")
        if scheme == "crypt":
            salt = "".join(Random().sample(string.letters + string.digits, 2))
            result = crypt.crypt(raw_value, salt)
            prefix = "{CRYPT}"
        elif scheme == "md5":
            obj = hashlib.md5(raw_value)
            result = obj.hexdigest()
            prefix = "{MD5}"
        # The md5crypt scheme is the only supported method that has both:
        # (a) a salt ("crypt" has this too),
        # (b) supports passwords lengths of more than 8 characters (all except
        #     "crypt").
        elif scheme == "md5crypt":
            # The salt may vary from 12 to 48 bits. (Using all six bytes here
            # with a subset of characters means we get only 35 random bits.)
            salt = "".join(Random().sample(string.letters + string.digits, 6))
            result = md5crypt(raw_value, salt)
            prefix = "" # the result already has $1$ prepended to it to signify what this is
        elif scheme == "sha256":
            obj = hashlib.sha256(raw_value)
            result = base64.b64encode(obj.digest())
            prefix = "{SHA256}"
        else:
            scheme = "plain"
            result = raw_value
            prefix = "{PLAIN}"
        return "%s%s" % (prefix, result)

    def set_password(self, raw_value, curvalue=None):
        """Password update

        Update the current mailbox's password with the given clear
        value. This value is encrypted according to the defined method
        before it is saved.

        :param raw_value: the new password's value
        :param curvalue: the current password (for LDAP authentication)
        """
        if parameters.get_admin("AUTHENTICATION_TYPE") == "local":
            self.password = self._crypt_password(raw_value)
            return

        if not ldap_available:
            raise AdminError(_("Failed to update password: LDAP module not installed"))

        ab = LDAPAuthBackend()
        try:
            ab.update_user_password(self.username, curvalue, raw_value)
        except LDAPException, e:
            raise AdminError(_("Failed to update password: %s" % str(e)))

    def check_password(self, raw_value):
        m = self.password_expr.match(self.password)
        if m is None:
            return False
        if type(raw_value) is unicode:
            raw_value = raw_value.encode("utf-8")
        scheme = (m.group(2) or m.group(3)).lower()
        val2 = m.group(4)
        if scheme == u"crypt":
            val1 = crypt.crypt(raw_value, val2)
        elif scheme == u"md5":
            val1 = hashlib.md5(raw_value).hexdigest()
        elif scheme == u"sha256":
            val1 = base64.b64encode(hashlib.sha256(raw_value).digest())
        elif scheme == u"$1$": # md5crypt
            salt, hashed = val2.split('$')
            val1 = md5crypt(raw_value, str(salt))
            val2 = self.password # re-add scheme for comparison below
        else:
            val1 = raw_value
        return constant_time_compare(val1, val2)

    @property
    def tags(self):
        return [{"name" : "account", "label" : _("account"), "type" : "idt"},
                {"name" : self.group, "label" : self.group, "type" : "grp", "color" : "info"}]

    @property
    def has_mailbox(self):
        return self.mailbox_set.count() != 0

    @property
    def fullname(self):
        if self.first_name != "":
            return u"%s %s" % (self.first_name, self.last_name)
        return self.username

    @property
    def identity(self):
        return self.username

    @property
    def name_or_rcpt(self):
        if self.first_name != "":
            return "%s %s" % (self.first_name, self.last_name)
        return "----"

    @property
    def group(self):
        if self.is_superuser:
            return "SuperAdmins"
        try:
            return self.groups.all()[0].name
        except IndexError:
            return "?"

    @property
    def enabled(self):
        return self.is_active

    def belongs_to_group(self, name):
        """Simple shortcut to check if this user is a member of a
        specific group.

        :param name: the group's name
        :return: a boolean
        """
        try:
            self.groups.get(name=name)
        except Group.DoesNotExist:
            return False
        return True

    def get_identities(self, querydict=None):
        """Return all identities owned by this user

        :param querydict: a querydict object
        :return: a queryset
        """
        from modoboa.lib.permissions import get_content_type
        from itertools import chain

        if querydict:
            squery = querydict.get("searchquery", None)
            idtfilter = querydict.getlist("idtfilter", None)
            grpfilter = querydict.getlist("grpfilter", None)
        else:
            squery = None
            idtfilter = None
            grpfilter = None

        accounts = []
        if not idtfilter or "account" in idtfilter:
            userct = get_content_type(self)
            ids = self.objectaccess_set.filter(content_type=userct) \
                .values_list('object_id', flat=True)
            q = Q(pk__in=ids)
            if squery:
                q &= Q(username__contains=squery)
            if grpfilter and len(grpfilter):
                if "SuperAdmins" in grpfilter:
                    q &= Q(is_superuser=True)
                    grpfilter.remove("SuperAdmins")
                    if len(grpfilter):
                        q |= Q(groups__name__in=grpfilter)
                else:
                    q &= Q(groups__name__in=grpfilter)
            accounts = User.objects.select_related().filter(q)

        aliases = []
        if not idtfilter or ("alias" in idtfilter 
                             or "forward" in idtfilter 
                             or "dlist" in idtfilter):
            alct = get_content_type(Alias)
            ids = self.objectaccess_set.filter(content_type=alct) \
                .values_list('object_id', flat=True)
            q = Q(pk__in=ids)
            if squery:
                if squery.find('@') != -1:
                    local_part, domname = split_mailbox(squery)
                    q &= Q(address__contains=local_part, domain__name__contains=domname)
                else:
                    q &= Q(address__contains=squery)
            aliases = Alias.objects.select_related().filter(q)
            if idtfilter:
                aliases = filter(lambda a: a.type in idtfilter, aliases)

        return chain(accounts, aliases)

    def get_domains(self):
        """Return the domains belonging to this user
        
        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if self.is_superuser:
            return Domain.objects.all()
        return Domain.objects.filter(owners__user=self)

    def get_domaliases(self):
        """Return the domain aliases that belong to this user
        
        The result will contain the domain aliases defined for each domain
        that user can see.
        
        :return: a list of ``DomainAlias`` objects
        """
        if self.is_superuser:
            return DomainAlias.objects.all()
        domains = self.get_domains()
        domaliases = []
        for dom in domains:
            domaliases += dom.domainalias_set.all()
        return domaliases

    def get_mailboxes(self, squery=None):
        """Return the mailboxes that belong to this user
        
        The result will contain the mailboxes defined for each domain that
        user can see.
        
        :param string squery: a search query
        :return: a list of ``Mailbox`` objects
        """
        from modoboa.lib.permissions import get_content_type

        qf = None
        if squery is not None:
            if '@' in squery:
                parts = squery.split('@')
                addrfilter = '@'.join(parts[:-1])
                domfilter = parts[-1]
                qf = Q(address__contains=addrfilter) & Q(domain__name__contains=domfilter)
            else:
                qf = Q(address__contains=squery) | Q(domain__name__contains=squery)
        ids = self.objectaccess_set.filter(content_type=get_content_type(Mailbox)) \
            .values_list('object_id', flat=True)
        if qf is not None:
            qf = Q(pk__in=ids) & qf
        else:
            qf = Q(pk__in=ids)
        return Mailbox.objects.filter(qf)
        
    def get_mbaliases(self):
        """Return the mailbox aliases that belong to this user
        
        The result will contain the mailbox aliases defined for each
        domain that user can see.
        
        :return: a list of ``Alias`` objects
        """
        if self.is_superuser:
            return Alias.objects.all()
        domains = self.get_domains()
        mbaliases = []
        for dom in domains:
            mbaliases += dom.alias_set.all()
        return mbaliases

    def is_owner(self, obj):
        """Tell is the user is the unique owner of this object

        :param obj: an object inheriting from ``models.Model``
        :return: a boolean
        """
        from modoboa.lib.permissions import get_content_type

        ct = get_content_type(obj)
        try:
            ooentry = self.objectaccess_set.get(content_type=ct, object_id=obj.id)
        except ObjectAccess.DoesNotExist:
            return False
        return ooentry.is_owner

    def can_access(self, obj):
        """Check if the user can access a specific object

        This function is recursive : if the given user hasn't got direct
        access to this object and if he has got access other ``User``
        objects, we check if one of those users owns the object.
        
        :param obj: a admin object
        :return: a boolean
        """
        from modoboa.lib.permissions import get_content_type

        if self.is_superuser:
            return True

        ct = get_content_type(obj)
        try:
            ooentry = self.objectaccess_set.get(content_type=ct, object_id=obj.id)
        except ObjectAccess.DoesNotExist:
            pass
        else:
            return True
        if ct.model == "user":
            return False

        ct = self.get_content_type()
        qs = self.objectaccess_set.filter(content_type=ct)
        for ooentry in qs.all():
            if ooentry.content_object.is_owner(obj):
                return True
        return False

    def grant_access_to_all_objects(self):
        """Give access to all objects defined in the database

        Must be used when an account is promoted as a super user.
        """
        from modoboa.lib.permissions import grant_access_to_objects, get_content_type
        grant_access_to_objects(self, User.objects.all(), get_content_type(User))
        grant_access_to_objects(self, Domain.objects.all(), get_content_type(Domain))
        grant_access_to_objects(self, DomainAlias.objects.all(), get_content_type(DomainAlias))
        grant_access_to_objects(self, Mailbox.objects.all(), get_content_type(Mailbox))
        grant_access_to_objects(self, Alias.objects.all(), get_content_type(Alias))

    def set_role(self, role):
        """Set administrative role for this account

        :param string role: the role to set
        """
        if role is None or self.group == role:
            return
        self.groups.clear()
        if role == "SuperAdmins":
            self.is_superuser = True
            self.grant_access_to_all_objects()
        else:
            if self.is_superuser:
                ObjectAccess.objects.filter(user=self).delete()
            self.is_superuser = False
            try:
                self.groups.add(Group.objects.get(name=role))
            except Group.DoesNotExist:
                self.groups.add(Group.objects.get(name="SimpleUsers"))
        self.save()

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("AccountCreated", self)

    def save(self, *args, **kwargs):
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(User, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def from_csv(self, user, row, crypt_password=True):
        """Create a new account from a CSV file entry

        The expected order is the following::

          loginname, password, first name, last name, enabled, group, address[, domain, ...]

        :param user: 
        :param row: a list containing the expected information
        :param crypt_password:
        """
        if len(row) < 6:
            raise AdminError(_("Invalid line"))
        role = row[6].strip()
        if not user.is_superuser and not role in ["SimpleUsers", "DomainAdmins"]:
            raise PermDeniedException(
                _("You can't import an account with a role greater than yours")
            )
        self.username = row[1].strip()
        if crypt_password:
            self.set_password(row[2].strip())
        else:
            self.password = row[2].strip()
        self.first_name = row[3].strip()
        self.last_name = row[4].strip()
        self.is_active = (row[5].strip() == 'True')
        self.save(creator=user)
        self.set_role(role)

        self.email = row[7].strip()
        if self.email != "":
            mailbox, domname = split_mailbox(self.email)
            try:
                domain = Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                raise AdminError(
                    _("Account import failed (%s): domain does not exist" % self.username)
                )
            if not user.can_access(domain):
                raise PermDeniedException
            mb = Mailbox(address=mailbox, domain=domain, user=self, use_domain_quota=True)
            mb.set_quota(override_rules=user.has_perm("admin.change_domain"))
            mb.save(creator=user)
        if self.group == "DomainAdmins":
            for domname in row[8:]:
                try:
                    dom = Domain.objects.get(name=domname.strip())
                except Domain.DoesNotExist:
                    continue
                dom.add_admin(self)

    def to_csv(self, csvwriter):
        row = ["account", self.username.encode("utf-8"), self.password, 
               self.first_name.encode("utf-8"), self.last_name.encode("utf-8"), 
               self.is_active, self.group, self.email]
        if self.group == "DomainAdmins":
            row += [dom.name for dom in self.get_domains()]
        csvwriter.writerow(row)


class ObjectAccess(models.Model):
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    is_owner = models.BooleanField(default=False)

    class Meta:
        unique_together = (("user", "content_type", "object_id"),)

    def __unicode__(self):
        return "%s => %s (%s)" % (self.user, self.content_object, self.content_type)


class ObjectDates(models.Model):
    """Dates recording for admin objects

    This table keeps creation and last modification dates for Domains,
    domain aliases, mailboxes and aliases objects.
    """
    creation = models.DateTimeField(auto_now_add=True)
    last_modification = models.DateTimeField(auto_now=True)

    @staticmethod
    def set_for_object(obj):
        """Initialize or update dates for a given object.

        :param obj: an admin object (Domain, Mailbox, etc)
        """
        try:
            dates = getattr(obj, "dates")
        except ObjectDates.DoesNotExist:
            dates = ObjectDates()
        dates.save()
        obj.dates = dates

class DatesAware(models.Model):
    """Abstract model to support dates

    Inherit from this model to automatically add the "dates" feature
    to another model. It defines the appropriate field and handles
    saves.
    """
    dates = models.ForeignKey(ObjectDates)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        ObjectDates.set_for_object(self)
        super(DatesAware, self).save(*args, **kwargs)

    @property
    def creation(self):
        return self.dates.creation

    @property
    def last_modification(self):
        return self.dates.last_modification


class Domain(DatesAware):
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

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
        )
        ordering = ["name"]

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
        ungrant_access_to_object(account, self)
        for mb in self.mailbox_set.all():
            if mb.user.has_perm("admin.add_domain"):
                continue
            ungrant_access_to_object(mb, account)
            ungrant_access_to_object(mb.user, account)
        for al in self.alias_set.all():
            ungrant_access_to_object(al, account)

    def delete(self, fromuser, keepdir=False):
        from modoboa.lib.permissions import ungrant_access_to_object, ungrant_access_to_objects

        if self.domainalias_set.count():
            events.raiseEvent("DomainAliasDeleted", self.domainalias_set.all())
            ungrant_access_to_objects(self.domainalias_set.all())
        if self.mailbox_set.count():
            Quota.objects.filter(username__contains='@%s' % self.name).delete()
            events.raiseEvent("DeleteMailbox", self.mailbox_set.all())
            ungrant_access_to_objects(self.mailbox_set.all())
            hm = parameters.get_admin("HANDLE_MAILBOXES", raise_error=False) 
            if hm == "yes" and not keepdir:
                for mb in self.mailbox_set.all():
                    mb.delete_dir()
        if self.alias_set.count():
            events.raiseEvent("MailboxAliasDelete", self.alias_set.all())
            ungrant_access_to_objects(self.alias_set.all())
        if parameters.get_admin("AUTO_ACCOUNT_REMOVAL") == "yes":
            for account in User.objects.filter(mailbox__domain__name=self.name):
                account.delete(fromuser, keepdir)
        events.raiseEvent("DeleteDomain", self)
        ungrant_access_to_object(self)
        super(Domain, self).delete()

    def __str__(self):
        return self.name

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("CreateDomain", creator, self)

    def save(self, *args, **kwargs):
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(Domain, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def from_csv(self, user, row):
        if len(row) < 4:
            raise AdminError(_("Invalid line"))
        self.name = row[1].strip()
        self.quota = int(row[2].strip())
        self.enabled = (row[3].strip() == 'True')
        self.save(creator=user)

    def to_csv(self, csvwriter):
        csvwriter.writerow(["domain", self.name, self.quota, self.enabled])


class DomainAlias(DatesAware):
    name = models.CharField(ugettext_lazy("name"), max_length=100, unique=True,
                            help_text=ugettext_lazy("The alias name"))
    target = models.ForeignKey(
        Domain, verbose_name=ugettext_lazy('target'),
        help_text=ugettext_lazy("The domain this alias points to")
    )
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to activate this alias")
    )

    class Meta:
        permissions = (
            ("view_domaliases", "View domain aliases"),
        )

    def __unicode__(self):
        return self.name

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("DomainAliasCreated", creator, self)

    def save(self, *args, **kwargs):
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(DomainAlias, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def delete(self):
        from modoboa.lib.permissions import ungrant_access_to_object
        events.raiseEvent("DomainAliasDeleted", self)
        ungrant_access_to_object(self)
        super(DomainAlias, self).delete()

    def from_csv(self, user, row):
        """Create a domain alias from a CSV row

        Expected format: ["domainalias", domain alias name, targeted domain, enabled]

        :param user: a ``User`` object
        :param row: a list containing the alias definition
        """
        if len(row) < 4:
            raise AdminError(_("Invalid line"))
        self.name = row[1].strip()
        domname = row[2].strip()
        try:
            self.target = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Unknown domain %s" % domname))
        self.enabled = row[3].strip() == 'True'
        self.save(creator=user)

    def to_csv(self, csvwriter):
        """Export a domain alias using CSV format

        :param csvwriter: a ``csv.writer`` object
        """
        csvwriter.writerow(["domainalias", self.name, self.target.name, self.enabled])


class Mailbox(DatesAware):
    address = models.CharField(
        ugettext_lazy('address'), max_length=100,
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
    def name_and_address(self):
        if self.user.first_name != "" or self.user.last_name != "":
            return "%s %s <%s>" % \
                (self.user.first_name, self.user.last_name, self.full_address)
        return self.full_address

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
        code, output = exec_cmd("mv %s %s" % (old_mail_home, self.mail_home), 
                                sudo_user=parameters.get_admin("MAILBOXES_OWNER"))
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
        code, output = exec_cmd("rm -r %s" % self.mail_home, 
                                sudo_user=parameters.get_admin("MAILBOXES_OWNER"))
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
    username = models.EmailField(primary_key=True)
    bytes = models.IntegerField(default=0)
    messages = models.IntegerField(default=0)

    mbox = models.OneToOneField(Mailbox, related_name="quota_value", null=True)


class Alias(DatesAware):
    address = models.CharField(
        ugettext_lazy('address'), max_length=254,
        help_text=ugettext_lazy("The alias address (without the domain part). For a 'catch-all' address, just enter an * character.")
        )
    domain = models.ForeignKey(Domain)
    mboxes = models.ManyToManyField(
        Mailbox, verbose_name=ugettext_lazy('mailboxes'),
        help_text=ugettext_lazy("The mailboxes this alias points to")
        )
    extmboxes = models.TextField(blank=True)
    enabled = models.BooleanField(ugettext_lazy('enabled'),
                                  help_text=ugettext_lazy("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )
        unique_together = (("address", "domain"),)
        ordering = ["domain__name", "address"]

    @property
    def full_address(self):
        return "%s@%s" % (self.address, self.domain.name)

    @property
    def identity(self):
        return self.full_address

    @property
    def name_or_rcpt(self):
        rcpts_count = self.get_recipients_count()
        if not rcpts_count:
            return "---"
        rcpts = self.get_recipients()
        if rcpts_count > 1:
            return "%s, ..." % rcpts[0]
        return rcpts[0]

    @property
    def type(self):
        cpt = self.get_recipients_count()
        if cpt > 1:
            return "dlist"
        if self.extmboxes != "":
            return "forward"
        return "alias"

    @property
    def tags(self):
        labels = {
            "dlist" : _("distribution list"),
            "forward" : _("forward"),
            "alias" : _("alias")
            }
        altype = self.type
        return [{"name" : altype, "label" : labels[altype], "type" : "idt"}]

    def post_create(self, creator):
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("MailboxAliasCreated", creator, self)
        if creator.is_superuser:
            for admin in self.domain.admins:
                grant_access_to_object(admin, self)

    def save(self, int_rcpts, ext_rcpts, *args, **kwargs):
        if len(ext_rcpts):
            self.extmboxes = ",".join(ext_rcpts)
        else:
            self.extmboxes = ""
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(Alias, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)
        curmboxes = self.mboxes.all()
        for t in int_rcpts:
            if not t in curmboxes:
                self.mboxes.add(t)
        for t in curmboxes:
            if not t in int_rcpts:
                self.mboxes.remove(t)

    def delete(self):
        from modoboa.lib.permissions import ungrant_access_to_object

        events.raiseEvent("MailboxAliasDeleted", self)
        ungrant_access_to_object(self)
        super(Alias, self).delete()

    def get_recipients(self):
        """Return the recipients list

        Internal and external addresses are mixed into a single list.
        """
        result = map(lambda mb: mb.full_address, self.mboxes.all())
        if self.extmboxes != "":
            result += self.extmboxes.split(',')
        return result

    def get_recipients_count(self):
        if self.extmboxes != "":
            return self.mboxes.count() + len(self.extmboxes.split(','))
        return self.mboxes.count()

    def ui_disabled(self, user):
        if user.is_superuser:
            return False
        for mb in self.mboxes.all():
            if not user.is_owner(mb.domain):
                return True
        return False

    def from_csv(self, user, row, expected_elements=5):
        if len(row) < expected_elements:
            raise AdminError(_("Invalid line: %s" % row))
        localpart, domname = split_mailbox(row[1].strip())
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Domain does not exist"))
        if not user.can_access(domain):
            raise PermDeniedException
        self.address = localpart
        self.domain = domain
        self.enabled = (row[2].strip() == 'True')
        int_rcpts = []
        ext_rcpts = []
        for rcpt in row[3:]:
            rcpt = rcpt.strip()
            localpart, domname = split_mailbox(rcpt)
            try:
                Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                ext_rcpts += [rcpt]
                continue
            try:
                int_rcpts += [Mailbox.objects.get(address=localpart, 
                                                  domain__name=domname)]
            except Mailbox.DoesNotExist:
                raise AdminError(_("Mailbox %s does not exist" % rcpt))
        self.save(int_rcpts, ext_rcpts, creator=user)

    def to_csv(self, csvwriter):
        row = [self.type, self.full_address, self.enabled]
        row += self.get_recipients()
        csvwriter.writerow(row)

class Extension(models.Model):
    name = models.CharField(max_length=150)
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to enable this extension")
        )

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

    def __get_ext_instance(self):
        if not self.name:
            return None
        if hasattr(self, "instance") and self.instance:
            return
        self.instance = exts_pool.get_extension(self.name)
        if self.instance:
            self.__get_ext_dir()

    def __get_ext_dir(self):
        modname = self.instance.__module__
        path = os.path.realpath(sys.modules[modname].__file__)
        self.extdir = os.path.dirname(path)

    def on(self):
        self.enabled = True
        self.save()

        self.__get_ext_instance()
        self.instance.load()
        self.instance.init()

        if self.instance.needs_media:
            path = os.path.join(settings.MEDIA_ROOT, self.name)
            exec_cmd("mkdir %s" % path)

        events.raiseEvent("ExtEnabled", self)

    def off(self):
        self.__get_ext_instance()
        self.instance.destroy()

        self.enabled = False
        self.save()

        if self.instance.needs_media:
            path = os.path.join(settings.MEDIA_ROOT, self.name)
            exec_cmd("rm -r %s" % path)

        events.raiseEvent("ExtDisabled", self)

def populate_callback(user):
    """Populate callback

    If the LDAP authentication backend is in use, this callback will
    be called each time a new user authenticates succesfuly to
    Modoboa. This function is in charge of creating the mailbox
    associated to the provided ``User`` object.

    :param user: a ``User`` instance
    """
    from modoboa.lib.permissions import grant_access_to_object

    sadmins = User.objects.filter(is_superuser=True)
    user.set_role("SimpleUsers")
    user.post_create(sadmins[0])
    for su in sadmins[1:]:
        grant_access_to_object(su, user)

    localpart, domname = split_mailbox(user.username)
    try:
        domain = Domain.objects.get(name=domname)
    except Domain.DoesNotExist:
        domain = Domain(name=domname, enabled=True, quota=0)
        domain.save(creator=sadmin[0])
        for su in sadmins[1:]:
            grant_access_to_object(su, domain)
    try:
        mb = Mailbox.objects.get(domain=domain, address=localpart)
    except Mailbox.DoesNotExist:
        mb = Mailbox(address=localpart, domain=domain, user=user, use_domain_quota=True)
        mb.set_quota()
        mb.save(creator=sadmins[0])
        for su in sadmins[1:]:
            grant_access_to_object(su, mb)
