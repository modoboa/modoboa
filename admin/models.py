# coding: utf-8
from django.db import models, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User as DUser, UserManager, Group
from django.utils.translation import ugettext as _, ugettext_noop
from django.utils.crypto import constant_time_compare
from django.conf import settings
from modoboa.lib import parameters, events
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.sysutils import exec_cmd, exec_as_vuser
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions import get_ext_module
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

def get_content_type(obj):
    """Simple function that use the right method to retrieve a content type

    :param obj: a django model
    :return: a ``ContentType`` object
    """
    return obj.get_content_type() if hasattr(obj, "get_content_type") \
        else ContentType.objects.get_for_model(obj)

class User(DUser):
    """Proxy for the ``User`` model.

    It overloads the way passwords are stored into the database. The
    main reason to change this mechanism is to ensure the
    compatibility with the way Dovecot stores passwords.

    It also adds new attributes and methods.
    """
    class Meta:
        proxy = True

    password_expr = re.compile(r'\{(\w+)\}(.+)')

    def __unicode__(self):
        return u"%s %s" % (self.first_name, self.last_name)

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
            salt = ''.join(Random().sample(string.letters + string.digits, 2))
            result = crypt.crypt(raw_value, salt)
        elif scheme == "md5":
            obj = hashlib.md5(raw_value)
            result = obj.hexdigest()
        elif scheme == "sha256":
            obj = hashlib.sha256(raw_value)
            result = base64.b64encode(obj.digest())
        else:
            scheme = "plain"
            result = raw_value
        return "{%s}%s" % (scheme.upper(), result)

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
        scheme = m.group(1).lower()
        val2 = m.group(2)
        if scheme == "crypt":
            val1 = crypt.crypt(raw_value, m.group(2))
        elif scheme == "md5":
            val1 = hashlib.md5(raw_value).hexdigest()
        elif scheme == "sha256":
            val1 = base64.b64encode(hashlib.sha256(raw_value).digest())
        else:
            val1 = raw_value
        return constant_time_compare(val1, val2)

    @property
    def has_mailbox(self):
        return len(self.mailbox_set.all()) != 0

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

    def get_domains(self):
        """Return the domains belonging to this user
        
        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        
        :param user: a ``User`` object
        """
        if self.is_superuser:
            return Domain.objects.all()
        result = Domain.objects.filter(owners__user=self).distinct()

        userct = self.get_content_type()
        for entry in self.objectaccess_set.filter(content_type=userct):
            if not entry.content_object.belongs_to_group('DomainAdmins'):
                continue
            result |= entry.content_object.get_domains().distinct()
        return result

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
    
class ObjectAccess(models.Model):
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    is_owner = models.BooleanField(default=False)

    class Meta:
        unique_together = (("user", "content_type", "object_id"),)
            
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

    def __creation(self):
        return self.dates.creation

    def __last_modification(self):
        return self.dates.last_modification

    creation = property(__creation)
    last_modification = property(__last_modification)

class Domain(DatesAware):
    name = models.CharField(ugettext_noop('name'), max_length=100, unique=True,
                            help_text=ugettext_noop("The domain name"))
    quota = models.IntegerField(help_text=ugettext_noop("Default quota in MB applied to mailboxes"))
    enabled = models.BooleanField(ugettext_noop('enabled'),
                                  help_text=ugettext_noop("Check to activate this domain"))
    owners = generic.GenericRelation(ObjectAccess)

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
            )

    def __domainalias_count(self):
        return len(self.domainalias_set.all())
    domainalias_count = property(__domainalias_count)

    def __mailbox_count(self):
        return len(self.mailbox_set.all())
    mailbox_count = property(__mailbox_count)

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

    def delete(self, *args, **kwargs):
        keepdir = False
        if kwargs.has_key("keepdir"):
            keepdir = kwargs["keepdir"]
            del kwargs["keepdir"]
        # Not very optimized but currently, this is the simple way
        # I've found to delete all related objects (mailboxes, users
        # and aliases)!
        for mb in self.mailbox_set.all():
            mb.delete(keepdir=keepdir)
        super(Domain, self).delete(*args, **kwargs)
        if not keepdir:
            self.delete_dir()

    def save(self, *args, **kwargs):
        if not self.create_dir():
            raise AdminError(_("Failed to initialise domain, check permissions"))
        super(Domain, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class DomainAlias(DatesAware):
    name = models.CharField(ugettext_noop("name"), max_length=100, unique=True,
                            help_text=ugettext_noop("The alias name"))
    target = models.ForeignKey(Domain, verbose_name=ugettext_noop('target'),
                               help_text=ugettext_noop("The domain this alias points to"))
    enabled = models.BooleanField(ugettext_noop('enabled'),
                                  help_text=ugettext_noop("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_domaliases", "View domain aliases"),
            )

class Mailbox(DatesAware):
    address = models.CharField(
        ugettext_noop('address'), max_length=100,
        help_text=ugettext_noop("Mailbox address (without the @domain.tld part)")
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
        return self.__full_address()

    def __full_address(self):
        return "%s@%s" % (self.address, self.domain.name)
    full_address = property(__full_address)

    def __enabled(self):
        return self.user.is_active
    enabled = property(__enabled)

    def __full_path(self):
        path = os.path.join(parameters.get_admin("STORAGE_PATH"),
                            self.domain.name, self.address)
        return os.path.abspath(path)
    full_path = property(__full_path)

    def __alias_count(self):
        return len(self.alias_set.all())
    alias_count = property(__alias_count)

    def create_dir(self):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            relpath = "%s/%s" % (self.domain.name, self.address)
            abspath = os.path.join(parameters.get_admin("STORAGE_PATH"), relpath)
            if self.mbtype == "mbox":
                self.path = "%s/Inbox" % self.address
            else:
                self.path = "%s/" % self.address
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

    def rename_dir(self, domain, newaddress):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            if self.domain.name == domain and newaddress == self.address:
                return True
            path = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), domain)
            code = exec_as_vuser("mv %s/%s %s/%s" \
                                     % (path, self.address, path, newaddress))
            if code:
                self.path = "%s/" % newaddress
            return code

        return True

    def delete_dir(self):
        if parameters.get_admin("CREATE_DIRECTORIES") == "yes":
            return exec_as_vuser("rm -r %s/%s/%s" \
                                     % (parameters.get_admin("STORAGE_PATH"),
                                        self.domain.name, self.address))
        return True

    def save(self, *args, **kwargs):
        if not self.create_dir():
            raise AdminError(_("Failed to initialise mailbox, check permissions"))
        try:
            user = getattr(self, "user")
        except User.DoesNotExist:
            user = User()
        user.username = user.email = "%s@%s" % (self.address, self.domain.name)
        if kwargs.has_key("enabled"):
            user.is_active = kwargs["enabled"]
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
        except IntegrityError:
            raise AdminError(_("Mailbox with this address already exists"))
        self.user = user

        if len(user.groups.all()) == 0:
            user.groups.add(Group.objects.get(name="SimpleUsers"))
            user.save()

	# If we ever had numerical uid, don't resolve it
	v_uid = parameters.get_admin("VIRTUAL_UID");
	if v_uid.isdigit():
            self.uid = v_uid
	else:
            self.uid = pwd.getpwnam(parameters.get_admin("VIRTUAL_UID")).pw_uid
	# Just the same for gid
	v_gid = parameters.get_admin("VIRTUAL_GID")
	if v_gid.isdigit():
            self.gid = v_gid
	else:
            self.gid = pwd.getpwnam(parameters.get_admin("VIRTUAL_GID")).pw_gid

        if kwargs.has_key("quota") and kwargs["quota"] is not None \
                and int(kwargs["quota"]) < self.domain.quota:
            self.quota = kwargs["quota"]
        else:
            self.quota = self.domain.quota
        for kw in ["name", "enabled", "password", "quota"]:
            try:
                del kwargs[kw]
            except KeyError:
                pass
        super(Mailbox, self).save(*args, **kwargs)

    def save_from_user(self, localpart, domain, user):
        """Simple save method called for automatic creations

        :param localpart: the mailbox
        :param domain: the associated Domain object
        :param user: the associated User object
        """
        self.name = "%s %s" % (user.first_name, user.last_name)
        self.address = localpart
        self.domain = domain
        self.user = user
        if not self.create_dir():
            raise AdminError(_("Failed to initialise mailbox, check permissions"))
	# If we ever had numerical uid, don't resolve it
	v_uid = parameters.get_admin("VIRTUAL_UID");
	if v_uid.isdigit():
            self.uid = v_uid
	else:
            self.uid = pwd.getpwnam(parameters.get_admin("VIRTUAL_UID")).pw_uid
	# Just the same for gid
	v_gid = parameters.get_admin("VIRTUAL_GID")
	if v_gid.isdigit():
            self.gid = v_gid
	else:
            self.gid = pwd.getpwnam(parameters.get_admin("VIRTUAL_GID")).pw_gid
            self.quota = self.domain.quota
        super(Mailbox, self).save()

    def create_from_csv(self, user, line):
        """Create a new mailbox from a CSV file entry

        The expected order is the following::

          [loginname, password, first name, last name, address]

        :param line: a list containing the expected information
        """
        if len(line) < 4:
            raise AdminError(_("Invalid line"))
        mailbox, domname = split_mailbox(line[0])
        self.address = mailbox
        try:
            self.domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise AdminError(_("Cannot import this mailbox because the associated domain does not exist"))
        if not user.is_owner(self.domain):
            raise PermDeniedException(_("You don't have access to this domain"))

        name = "%s %s" % (line[2], line[3])
        self.save(name=name, password=line[1], enabled=True)

    def delete(self, *args, **kwargs):
        keepdir = False
        if kwargs.has_key("keepdir"):
            keepdir = kwargs["keepdir"]
            del kwargs["keepdir"]
        for alias in self.alias_set.all():
            alias.mboxes.remove(self)
            if len(alias.mboxes.all()) == 0:
                alias.delete()
        self.user.delete()
        super(Mailbox, self).delete(*args, **kwargs)
        if not keepdir:
            self.delete_dir()


class Alias(DatesAware):
    address = models.CharField(ugettext_noop('address'), max_length=254,
                               help_text=ugettext_noop("The alias address (without the domain part). For a 'catch-all' address, just enter an * character."))
    domain = models.ForeignKey(Domain)
    mboxes = models.ManyToManyField(Mailbox, verbose_name=ugettext_noop('mailboxes'),
                                    help_text=ugettext_noop("The mailboxes this alias points to"))
    extmboxes = models.TextField(blank=True)
    enabled = models.BooleanField(ugettext_noop('enabled'),
                                  help_text=ugettext_noop("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )

    def __full_address(self):
        return "%s@%s" % (self.address, self.domain.name)
    full_address = property(__full_address)

    def __targets(self):
        ret = "<br/>".join(map(lambda m: str(m), self.mboxes.all()))
        ret += "<br/>" + self.repr_extmboxes()
        return ret
    targets = property(__targets)

    def save(self, int_targets, ext_targets, *args, **kwargs):
        if len(ext_targets):
            self.extmboxes = ",".join(ext_targets)
        else:
            self.extmboxes = ""
        super(Alias, self).save(*args, **kwargs)
        curmboxes = self.mboxes.all()
        for t in int_targets:
            if not t in curmboxes:
                self.mboxes.add(t)
        for t in curmboxes:
            if not t in int_targets:
                self.mboxes.remove(t)

    def first_target(self):
        """Return the first target of this alias

        It is taken from internal addresses, or external addresses.
        """
        if len(self.mboxes.all()):
            return self.mboxes.all()[0]
        if len(self.extmboxes):
            return self.extmboxes.split(",")[0]
        return None

    def get_targets(self):
        """Return a list containing targeted mailboxes

        Internal and external addresses are mixed into a single list.
        """
        result = []
        if len(self.mboxes.all()):
            for mb in self.mboxes.all()[1:]:
                result += [mb.full_address]
            if len(self.extmboxes):
                result += self.extmboxes.split(",")
        else:
            result = self.extmboxes.split(",")[1:]
        return result

    def repr_extmboxes(self):
        """Return external targets as a string

        A ready to print representation of external targets.
        """
        return "<br/>".join(self.extmboxes.split(","))

    def ui_disabled(self, user):
        if user.is_superuser:
            return False
        for mb in self.mboxes.all():
            if not user.is_owner(mb.domain):
                return True
        return False

class Extension(models.Model):
    name = models.CharField(max_length=150)
    enabled = models.BooleanField(
        ugettext_noop('enabled'),
        help_text=ugettext_noop("Check to enable this extension")
        )

    def init(self):
        module = get_ext_module(self.name)
        if hasattr(module, "init"):
            module.init()

    def load(self):
        module = get_ext_module(self.name)
        if hasattr(module, "load"):
            module.load()

    def unload(self):
        module = get_ext_module(self.name)
        module.destroy()

    def on(self):
        self.load()
        self.init()
        self.enabled = True
        self.save()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            targetdir = os.path.join(settings.MODOBOA_DIR, "scripts")
            exec_cmd("ln -s %s %s/%s" % (scriptdir, targetdir, self.name))

        staticpath = "%s/%s" % (extdir, "static")
        if os.path.exists(staticpath):
            exec_cmd("ln -s %s/static %s/static/%s" % \
                         (extdir, settings.MODOBOA_DIR, self.name))

        events.raiseEvent("ExtEnabled", self)

    def off(self):
        self.unload()

        self.enabled = False
        self.save()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            target = "%s/scripts/%s" % (settings.MODOBOA_DIR, self.name)
            exec_cmd("rm %s" % target)

        staticpath = "%s/%s" % (extdir, "static")  
        if os.path.exists(staticpath):
            exec_cmd("rm -r %s/static/%s" % (settings.MODOBOA_DIR, self.name)) 

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
