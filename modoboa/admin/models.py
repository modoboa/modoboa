# coding: utf-8
from django.db import models, IntegrityError
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
from exceptions import *
import os, sys
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
        return u"%s %s" % (self.first_name, self.last_name)

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
        scheme = (m.group(2) or m.group(3)).lower()
        val2 = m.group(4)
        if scheme == "crypt":
            val1 = crypt.crypt(raw_value, val2)
        elif scheme == "md5":
            val1 = hashlib.md5(raw_value).hexdigest()
        elif scheme == "sha256":
            val1 = base64.b64encode(hashlib.sha256(raw_value).digest())
        elif scheme == "$1$": # md5crypt
            salt, hashed = val2.split('$')
            val1 = md5crypt(raw_value, salt)
            val2 = self.password # re-add scheme for comparison below
        else:
            val1 = raw_value
        return constant_time_compare(val1, val2)

    @property
    def tags(self):
        ret = '<span class="label">%s</span>' % _("account")
        ret += ' <span class="label label-info">%s</span>' % self.group
        return ret

    @property
    def has_mailbox(self):
        return len(self.mailbox_set.all()) != 0

    @property
    def fullname(self):
        if self.first_name != "":
            return "%s %s" % (self.first_name, self.last_name)
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

    def get_identities(self):
        from modoboa.lib.permissions import get_content_type
    
        userct = get_content_type(self)
        alct = get_content_type(Alias)
        return self.objectaccess_set.filter(content_type__in=[userct, alct])

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

    def get_mailboxes(self):
        """Return the mailboxes that belong to this user
        
        The result will contain the mailboxes defined for each domain that
        user can see.
        
        :return: a list of ``Mailbox`` objects
        """
        if self.is_superuser:
            return Mailbox.objects.all()
        mboxes = []
        domains = self.get_domains()
        for dom in domains:
            mboxes += dom.mailbox_set.all()
        return mboxes
        
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

    def to_csv(self, csvwriter):
        csvwriter.writerow(["account", self.username.encode("utf-8"), self.password, 
                            self.first_name.encode("utf-8"), self.last_name.encode("utf-8"), 
                            self.email])
    
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
    quota = models.IntegerField(help_text=ugettext_lazy("Default quota in MB applied to mailboxes"))
    enabled = models.BooleanField(ugettext_lazy('enabled'),
                                  help_text=ugettext_lazy("Check to activate this domain"))
    owners = generic.GenericRelation(ObjectAccess)

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
            )
        ordering = ["name"]
        
    @property
    def domainalias_count(self):
        return len(self.domainalias_set.all())

    @property
    def mailbox_count(self):
        return len(self.mailbox_set.all())

    @property
    def mbalias_count(self):
        return len(self.alias_set.all())

    @property
    def admins(self):
        return [oa.user for oa in self.owners.filter(user__is_superuser=False)]
        
    def create_dir(self):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            path = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), self.name)
            return exec_as_vuser("mkdir -p %s" % path)
        
        return True

    def rename_dir(self, oldname):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            stpath = parameters.get_admin("STORAGE_PATH")
            return exec_as_vuser("mv %s/%s %s/%s" \
                                     % (stpath, oldname, stpath, self.name))
        return True

    def delete_dir(self):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            return exec_as_vuser("rm -r %s/%s" \
                                     % (parameters.get_admin("STORAGE_PATH"), 
                                        self.name))
        return True

    def delete(self, keepdir=False):
        from modoboa.lib.permissions import ungrant_access_to_object, ungrant_access_to_objects

        if len(self.domainalias_set.all()):
            events.raiseEvent("DomainAliasDeleted", self.domainalias_set.all())
            ungrant_access_to_objects(self.domainalias_set.all())
        if len(self.mailbox_set.all()):
            events.raiseEvent("DeleteMailbox", self.mailbox_set.all())
            ungrant_access_to_objects(self.mailbox_set.all())
        if len(self.alias_set.all()):
            events.raiseEvent("MailboxAliasDelete", self.alias_set.all())
            ungrant_access_to_objects(self.alias_set.all())
        events.raiseEvent("DeleteDomain", self)
        ungrant_access_to_object(self)
        super(Domain, self).delete()
        if not keepdir:
            self.delete_dir()

    def save(self, *args, **kwargs):
        if not self.create_dir():
            raise AdminError(_("Failed to initialise domain, check permissions"))
        super(Domain, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def create_from_csv(self, user, row):
        if len(row) < 3:
            raise AdminError(_("Invalid line"))
        self.name = row[1].strip()
        self.quota = int(row[2].strip())
        self.enabled = True
        self.save()

    def to_csv(self, csvwriter):
        csvwriter.writerow(["domain", self.name, self.quota])

class DomainAlias(DatesAware):
    name = models.CharField(ugettext_lazy("name"), max_length=100, unique=True,
                            help_text=ugettext_lazy("The alias name"))
    target = models.ForeignKey(Domain, verbose_name=ugettext_lazy('target'),
                               help_text=ugettext_lazy("The domain this alias points to"))
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

    def delete(self):
        from modoboa.lib.permissions import ungrant_access_to_object
        events.raiseEvent("DomainAliasDeleted", self)
        ungrant_access_to_object(self)
        super(DomainAlias, self).delete()

    def to_csv(self, csvwriter):
        csvwriter.writerow(["domainalias", self.name, self.target.name])

class Mailbox(DatesAware):
    address = models.CharField(
        ugettext_lazy('address'), max_length=100,
        help_text=ugettext_lazy("Mailbox address (without the @domain.tld part)")
        )
    quota = models.IntegerField()
    uid = models.IntegerField()
    gid = models.IntegerField()
    path = models.CharField(max_length=255)
    domain = models.ForeignKey(Domain)
    user = models.ForeignKey(User)

    class Meta:
        permissions = (
            ("view_mailboxes", "View mailboxes"),
            )

    def __init__(self, *args, **kwargs):
        super(Mailbox, self).__init__(*args, **kwargs)
        self.mbtype = parameters.get_admin("MAILBOX_TYPE")
        self.mdirroot = parameters.get_admin("MAILDIR_ROOT")
        if not self.mdirroot.endswith('/'):
            self.mdirroot += '/'

    def __str__(self):
        return self.full_address
	
    @property
    def full_address(self):
        return "%s@%s" % (self.address, self.domain.name)

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
    def full_path(self):
        path = os.path.join(parameters.get_admin("STORAGE_PATH"),
                            self.domain.name, self.address)
        return os.path.abspath(path)

    @property
    def alias_count(self):
        return len(self.alias_set.all())

    def create_dir(self):
        if self.mbtype == "mbox":
            self.path = "%s/Inbox" % self.address
        else:
            self.path = "%s/" % self.address
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            relpath = "%s/%s" % (self.domain.name, self.address)
            abspath = os.path.join(parameters.get_admin("STORAGE_PATH"), relpath)
            if os.path.exists(abspath):
                return True
            if not exec_as_vuser("mkdir -p %s" % abspath):
                return False
            if self.mbtype == "mbox":
                template = ["Inbox", "Drafts", "Sent", "Trash", "Junk"]
                for f in template:
                    exec_as_vuser("touch %s/%s" % (abspath, f))
            else:
                template = [".Drafts/", ".Sent/", ".Trash/", ".Junk/"]
                for dir in template:
                    for sdir in ["cur", "new", "tmp"]:
                        exec_as_vuser("mkdir -p %s/%s/%s/%s" \
                                          % (abspath, self.mdirroot, dir, sdir))
        return True

    def rename_dir(self, newdomain, newaddress):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            if self.domain.name == newdomain and newaddress == self.address:
                return True
            oldpath = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), self.domain.name)
            newpath = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), newdomain)
            oldpath = os.path.join(oldpath, self.address)
            newpath = os.path.join(newpath, newaddress)
            code = exec_as_vuser("mv %s %s" % (oldpath, newpath))
            if code:
                self.path = "%s/" % newaddress
            return code
        else:
            self.path  ="%s/" % newaddress

        return True

    def delete_dir(self):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            return exec_as_vuser("rm -r %s/%s/%s" \
                                     % (parameters.get_admin("STORAGE_PATH"),
                                        self.domain.name, self.address))
        return True

    def set_ownership(self):
        # If we ever had numerical uid, don't resolve it
	v_uid = parameters.get_admin("VIRTUAL_UID");
	if v_uid.isdigit():
            self.uid = v_uid
	else:
            try:
                self.uid = pwd.getpwnam(v_uid).pw_uid
            except KeyError:
                raise AdminError(_("%s is not a valid uid/username" % v_uid))
	# Just the same for gid
	v_gid = parameters.get_admin("VIRTUAL_GID")
	if v_gid.isdigit():
            self.gid = v_gid
	else:
            try:
                self.gid = pwd.getpwnam(v_gid).pw_gid
            except KeyError:
                raise AdminError(_("%s is not a valid gid/groupname" % v_gid))

    def set_quota(self, value, override_domain=False):
        if value is None or (int(value) > self.domain.quota and not override_domain):
            self.quota = self.domain.quota
        else:
            self.quota = value

    def save(self, *args, **kwargs):
        if not self.create_dir():
            raise AdminError(_("Failed to initialise mailbox, check permissions"))
        try:
            user = getattr(self, "user")
        except User.DoesNotExist:
            user = User()
        user.email = "%s@%s" % (self.address, self.domain.name)
        if kwargs.has_key("username"):
            user.username = kwargs["username"]
        else:
            user.username = user.email
        if kwargs.has_key("enabled"):
            user.is_active = kwargs["enabled"]
        if kwargs.has_key("name"):
            try:
                fname, lname = kwargs["name"].split()
            except ValueError:
                fname = kwargs["name"]
                lname = ""
            user.first_name = fname
            user.last_name = lname
        if kwargs.has_key("password"):
            user.set_password(kwargs["password"])
        try:
            user.save()
        except IntegrityError, e:
            raise AdminError(_("Account '%s' already exists" % user.username))
        self.user = user

        if len(user.groups.all()) == 0:
            user.groups.add(Group.objects.get(name="SimpleUsers"))
            user.save()

        self.set_ownership()
        if kwargs.has_key("quota"):
            self.set_quota(kwargs["quota"])

        for kw in ["username", "name", "enabled", "password", "quota"]:
            try:
                del kwargs[kw]
            except KeyError:
                pass
        super(Mailbox, self).save(*args, **kwargs)

    def save_from_user(self, localpart, domain, user, quota=None, owner=None):
        """Simple save method called for automatic creations

        :param localpart: the mailbox
        :param domain: the associated Domain object
        :param user: the associated User object
        """
        self.address = localpart
        self.domain = domain
        self.user = user
        if not self.create_dir():
            raise AdminError(_("Failed to initialise mailbox, check permissions"))
        self.set_ownership()
        self.set_quota(quota, True if (owner and owner.has_perm("admin.add_domain")) else False)
        super(Mailbox, self).save()

    def create_from_csv(self, user, line):
        """Create a new mailbox from a CSV file entry

        The expected order is the following::

          [loginname, password, first name, last name, address]

        :param line: a list containing the expected information
        """
        if len(line) < 6:
            raise AdminError(_("Invalid line"))
        mailbox, domname = split_mailbox(line[5].strip())
        self.address = mailbox
        try:
            self.domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Cannot import this mailbox because the associated domain does not exist"))
        if not user.can_access(self.domain):
            raise PermDeniedException

        name = "%s %s" % (line[3].strip(), line[4].strip())
        self.save(username=line[1].strip(), name=name, 
                  password=line[2].strip(), enabled=True, quota=None)

    def delete(self, keepdir=False):
        from modoboa.lib.permissions import ungrant_access_to_object

        events.raiseEvent("DeleteMailbox", self)
        ungrant_access_to_object(self)
        for alias in self.alias_set.all():
            alias.mboxes.remove(self)
            if len(alias.mboxes.all()) == 0:
                alias.delete()
        super(Mailbox, self).delete()
        if not keepdir:
            self.delete_dir()


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
        rcpts = self.get_recipients()
        if len(rcpts) > 1:
            return "%s, ..." % rcpts[0]
        return rcpts[0]

    @property
    def tags(self):
        cpt = len(self.get_recipients())
        if cpt > 1:
            label = _("distribution list")
        elif self.extmboxes != "":
            label = _("forward")
        else:
            label = _("alias")
        return '<span class="label">%s</span>' % label

    def save(self, int_rcpts, ext_rcpts, *args, **kwargs):
        if len(ext_rcpts):
            self.extmboxes = ",".join(ext_rcpts)
        else:
            self.extmboxes = ""
        super(Alias, self).save(*args, **kwargs)
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

    def ui_disabled(self, user):
        if user.is_superuser:
            return False
        for mb in self.mboxes.all():
            if not user.is_owner(mb.domain):
                return True
        return False

    def create_from_csv(self, user, row, expected_elements=4):
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
        self.enabled = True
        int_rcpts = []
        ext_rcpts = []
        for rcpt in row[2:]:
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
        self.save(int_rcpts, ext_rcpts)        

    def to_csv(self, csvwriter):
        cpt = len(self.get_recipients())
        if cpt > 1:
            altype = "dlist"
        elif self.extmboxes != "":
            altype = "forward"
        else:
            altype = "alias"
        row = [altype, self.address]
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

def populate_callback(sender, user=None, **kwargs):
    """Populate signal callback

    If the LDAP authentication backend is in use, this callback will
    be called each time a new user authenticates succesfuly to
    Modoboa. This function is in charge of creating the mailbox
    associated to the provided ``User`` object.

    :param sender: ??
    :param user: a ``User`` instance
    """
    if parameters.get_admin("AUTHENTICATION_TYPE") != "ldap":
        return
    if user is None:
        return
    localpart, domname = split_mailbox(user.username)
    try:
        domain = Domain.objects.get(name=domname)
    except Domain.DoesNotExist:
        domain = Domain()
        domain.name = domname
        domain.enabled = True
        domain.quota = 0
        domain.save()
    try:
        mb = Mailbox.objects.get(domain=domain, address=localpart)
    except Mailbox.DoesNotExist:
        mb = Mailbox()
        mb.save_from_user(localpart, domain, user)

try:
    from django_auth_ldap.backend import populate_user
except ImportError, inst:
    pass
else:
    populate_user.connect(populate_callback, dispatch_uid="myuid")
