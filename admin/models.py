# coding: utf-8
from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _, ugettext_noop
from django.conf import settings
from modoboa.lib import parameters, events
from modoboa.lib.sysutils import exec_cmd, exec_as_vuser
from modoboa.lib.emailutils import split_mailbox
from modoboa.auth.lib import crypt_password
import os
import pwd

class AdminError(Exception):
    """Custom exception

    
    """
    def __init__(self, value):
        """Constructor

        :param value: the information contained in this exception.
        """
        self.value = str(value)
        
    def __str__(self):
        """String representation"""
        return self.value

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
    name = models.CharField(ugettext_noop('name'), max_length=100, 
                            help_text=ugettext_noop("First name and last name of mailbox owner"))
    address = models.CharField(ugettext_noop('address'), max_length=100,
                               help_text=ugettext_noop("Mailbox address (without the @domain.tld part)"))
    password = models.CharField(ugettext_noop('password'), max_length=100)
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
        user.set_unusable_password()
        if kwargs.has_key("enabled"):
            user.is_active = kwargs["enabled"]
        try:
            fname, lname = self.name.split()
        except ValueError:
            fname = self.name
            lname = ""
        user.first_name = fname
        user.last_name = lname
        try:
            user.save()
        except IntegrityError:
            raise AdminError(_("Mailbox with this address already exists"))
        self.user = user

        if kwargs.has_key("password") and kwargs["password"] != u"é":
            self.password = crypt_password(kwargs["password"])
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
        for kw in ["enabled", "password", "quota"]:
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
	if v_gid.isdigit:
		self.gid = v_gid
	else:
		self.gid = pwd.getpwnam(parameters.get_admin("VIRTUAL_GID")).pw_gid
        self.quota = self.domain.quota
        super(Mailbox, self).save()

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

    def tohash(self):
        return {
            "id" : self.id, 
            "domain" : self.domain.name,
            "full_name" : self.name,
            "date_joined" : self.user.date_joined,
            "enabled" : self.user.is_active
            }

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
        usermb = Mailbox.objects.get(user=user.id)
        for mb in self.mboxes.all():
            if mb.domain.id != usermb.domain.id:
                return True
        return False

class Extension(models.Model):
    name = models.CharField(max_length=150)
    enabled = models.BooleanField(ugettext_noop('enabled'),
                                  help_text=ugettext_noop("Check to enable this extension"))

    def __getmodule(self):
        extname = "modoboa.extensions.%s" % self.name
        return __import__(extname, globals(), locals(), ['main'])

    def load(self):
        self.__getmodule().main.init()

    def unload(self):
        self.__getmodule().main.destroy()

    def on(self):
        self.load()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            targetdir = os.path.join(settings.MODOBOA_DIR, "scripts")
            exec_cmd("ln -s %s %s/%s" % (scriptdir, targetdir, self.name))

        staticpath = "%s/%s" % (extdir, "static")
        if os.path.exists(staticpath):
            exec_cmd("ln -s %s/static %s/static/%s" % \
                         (extdir, settings.MODOBOA_DIR, self.name))

        events.raiseEvent("ExtEnabled", ext=self)

    def off(self):
        self.unload()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            target = "%s/scripts/%s" % (settings.MODOBOA_DIR, self.name)
            exec_cmd("rm %s" % target)

        staticpath = "%s/%s" % (extdir, "static")  
        if os.path.exists(staticpath):
            exec_cmd("rm -r %s/static/%s" % (settings.MODOBOA_DIR, self.name)) 

        events.raiseEvent("ExtDisabled", ext=self)

#
# Optional callback to execute if django-auth-ldap is enabled.
#
try:
    from django_auth_ldap.backend import populate_user

    def populate_callback(sender, user=None, **kwargs):
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

    populate_user.connect(populate_callback, dispatch_uid="myuid")

except ImportError, inst:
    pass
