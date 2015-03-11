import sys
import os
import re
import logging
import reversion
from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import (
    UserManager, Group, PermissionsMixin
)
from django.contrib.auth.hashers import make_password, is_password_usable
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import (
    PermDeniedException, InternalError, BadRequest, Conflict
)
from modoboa.lib.sysutils import exec_cmd
from modoboa.core.extensions import exts_pool
from modoboa.core.password_hashers import get_password_hasher

try:
    from modoboa.lib.ldaputils import LDAPAuthBackend
    ldap_available = True
except ImportError:
    ldap_available = False


class User(PermissionsMixin):
    """Custom User model.

    It overloads the way passwords are stored into the database. The
    main reason to change this mechanism is to ensure the
    compatibility with the way Dovecot stores passwords.

    It also adds new attributes and methods.
    """
    username = models.CharField(max_length=254, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_local = models.BooleanField(default=True)
    password = models.CharField(ugettext_lazy('password'), max_length=256)
    last_login = models.DateTimeField(
        ugettext_lazy('last login'), default=timezone.now
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ["username"]

    password_expr = re.compile(r'\{([\w\-]+)\}(.+)')

    def delete(self, fromuser, *args, **kwargs):
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
            raise PermDeniedException(
                _("You can't delete your own account")
            )

        if not fromuser.can_access(self):
            raise PermDeniedException

        owner = get_object_owner(self)
        for ooentry in self.objectaccess_set.filter(is_owner=True):
            if ooentry.content_object is not None:
                grant_access_to_object(owner, ooentry.content_object, True)
                ungrant_access_to_object(ooentry.content_object, self)

        events.raiseEvent("AccountDeleted", self, fromuser, **kwargs)
        ungrant_access_to_object(self)
        super(User, self).delete()

    def _crypt_password(self, raw_value):
        """Crypt the local password using the appropriate scheme.

        In case we don't find the scheme (for example when the
        management framework is used), we load the parameters and try
        one more time.

        """
        try:
            scheme = parameters.get_admin("PASSWORD_SCHEME")
        except parameters.NotDefined:
            from modoboa.core import load_core_settings
            load_core_settings()
            scheme = parameters.get_admin("PASSWORD_SCHEME")

        if type(raw_value) is unicode:
            raw_value = raw_value.encode("utf-8")
        return get_password_hasher(scheme.upper())().encrypt(raw_value)

    def set_password(self, raw_value, curvalue=None):
        """Password update

        Update the current mailbox's password with the given clear
        value. This value is encrypted according to the defined method
        before it is saved.

        :param raw_value: the new password's value
        :param curvalue: the current password (for LDAP authentication)
        """
        if self.is_local:
            self.password = self._crypt_password(raw_value)
        else:
            if not ldap_available:
                raise InternalError(
                    _("Failed to update password: LDAP module not installed")
                )
            LDAPAuthBackend().update_user_password(
                self.username, curvalue, raw_value
            )
        events.raiseEvent(
            "PasswordUpdated", self, raw_value, self.pk is None
        )

    def check_password(self, raw_value):
        match = self.password_expr.match(self.password)
        if match is None:
            return False
        if type(raw_value) is unicode:
            raw_value = raw_value.encode("utf-8")
        scheme = match.group(1)
        val2 = match.group(2)
        hasher = get_password_hasher(scheme)
        return hasher().verify(raw_value, val2)

    def get_username(self):
        "Return the identifying username for this User"
        return getattr(self, self.USERNAME_FIELD)

    def __str__(self):
        return self.get_username()

    def natural_key(self):
        return (self.get_username(),)

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(None)

    def has_usable_password(self):
        return is_password_usable(self.password)

    @property
    def tags(self):
        return [{"name": "account", "label": _("account"), "type": "idt"},
                {"name": self.group, "label": self.group,
                 "type": "grp", "color": "info"}]

    @property
    def fullname(self):
        if self.first_name != u"":
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
            return "---"

    @property
    def enabled(self):
        return self.is_active

    @property
    def encoded_address(self):
        from email.header import Header
        if self.first_name != "" or self.last_name != "":
            return "%s <%s>" % \
                (Header(self.fullname, 'utf8').encode(), self.email)
        return self.email

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

    def is_owner(self, obj):
        """Tell is the user is the unique owner of this object

        :param obj: an object inheriting from ``models.Model``
        :return: a boolean
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            ooentry = self.objectaccess_set.get(content_type=ct, object_id=obj.id)
        except ObjectAccess.DoesNotExist:
            return False
        return ooentry.is_owner

    def can_access(self, obj):
        """Check if the user can access a specific object

        This function is recursive: if the given user hasn't got
        direct access to this object and if he has got access to other
        ``User`` objects, we check if one of those users owns the
        object.

        :param obj: a admin object
        :return: a boolean
        """
        if self.is_superuser:
            return True

        ct = ContentType.objects.get_for_model(obj)
        try:
            ooentry = self.objectaccess_set.get(content_type=ct, object_id=obj.id)
        except ObjectAccess.DoesNotExist:
            pass
        else:
            return True
        if ct.model == "user":
            return False

        ct = ContentType.objects.get_for_model(self)
        qs = self.objectaccess_set.filter(content_type=ct)
        for ooentry in qs.all():
            if ooentry.content_object.is_owner(obj):
                return True
        return False

    def set_role(self, role):
        """Set administrative role for this account

        :param string role: the role to set
        """
        if role is None or self.group == role:
            return
        events.raiseEvent("RoleChanged", self, role)
        self.groups.clear()
        if role == "SuperAdmins":
            self.is_superuser = True
        else:
            if self.is_superuser:
                ObjectAccess.objects.filter(user=self).delete()
            self.is_superuser = False
            try:
                self.groups.add(Group.objects.get(name=role))
            except Group.DoesNotExist:
                self.groups.add(Group.objects.get(name="SimpleUsers"))
            if self.group != "SimpleUsers" and not self.can_access(self):
                from modoboa.lib.permissions import grant_access_to_object
                grant_access_to_object(self, self)
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
        """Create a new account from a CSV file entry.

        The expected order is the following::

        "account", loginname, password, first name, last name, enabled, group

        Additional fields can be added using the *AccountImported* event.

        :param user: a ``core.User`` instance
        :param row: a list containing the expected information
        :param crypt_password:
        """
        if len(row) < 7:
            raise BadRequest(_("Invalid line"))
        role = row[6].strip()
        if not user.is_superuser and not role in ["SimpleUsers", "DomainAdmins"]:
            raise PermDeniedException(
                _("You can't import an account with a role greater than yours")
            )
        self.username = row[1].strip()
        try:
            User.objects.get(username=self.username)
        except User.DoesNotExist:
            pass
        else:
            raise Conflict
        if role == "SimpleUsers":
            if (len(row) < 8 or not row[7].strip()):
                raise BadRequest(
                    _("The simple user '%s' must have a valid email address" % self.username)
                )
            if self.username != row[7].strip():
                raise BadRequest(
                    _("username and email fields must not differ for '%s'" % self.username)
                )

        if crypt_password:
            self.set_password(row[2].strip())
        else:
            self.password = row[2].strip()
        self.first_name = row[3].strip()
        self.last_name = row[4].strip()
        self.is_active = (row[5].strip() in ["True", "1", "yes", "y"])
        self.save(creator=user)
        self.set_role(role)
        if len(row) < 8:
            return
        events.raiseEvent("AccountImported", user, self, row[7:])

    def to_csv(self, csvwriter):
        """Export this account.

        The CSV format is used to export.

        :param csvwriter: csv object
        """
        row = ["account", self.username.encode("utf-8"), self.password.encode("utf-8"),
               self.first_name.encode("utf-8"), self.last_name.encode("utf-8"),
               self.is_active, self.group, self.email.encode("utf-8")]
        row += events.raiseQueryEvent("AccountExported", self)
        csvwriter.writerow(row)

reversion.register(User)


def populate_callback(user, group='SimpleUsers'):
    """Populate callback

    If the LDAP authentication backend is in use, this callback will
    be called each time a new user authenticates succesfuly to
    Modoboa. This function is in charge of creating the mailbox
    associated to the provided ``User`` object.

    :param user: a ``User`` instance
    """
    from modoboa.lib.permissions import grant_access_to_object

    sadmins = User.objects.filter(is_superuser=True)
    user.set_role(group)
    user.post_create(sadmins[0])
    for su in sadmins[1:]:
        grant_access_to_object(su, user)
    events.raiseEvent("AccountAutoCreated", user)


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


class Extension(models.Model):

    """A modoboa extension."""

    name = models.CharField(max_length=150)
    enabled = models.BooleanField(
        ugettext_lazy('enabled'),
        help_text=ugettext_lazy("Check to enable this extension")
    )

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name

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

    def on(self, update_db=True):
        """Activate this extension."""
        if update_db:
            self.enabled = True
            self.save()

        self.__get_ext_instance()
        self.instance.load()
        self.instance.init()

        if self.instance.needs_media:
            path = os.path.join(settings.MEDIA_ROOT, self.name)
            exec_cmd("mkdir %s" % path)

        events.raiseEvent("ExtEnabled", self)

    def off(self, update_db=True):
        """Disable this extension."""
        self.__get_ext_instance()
        if self.instance is None:
            return
        self.instance.destroy()

        if update_db:
            self.enabled = False
            self.save()

        if self.instance.needs_media:
            path = os.path.join(settings.MEDIA_ROOT, self.name)
            exec_cmd("rm -r %s" % path)

        events.raiseEvent("ExtDisabled", self)

reversion.register(Extension)


class Log(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    level = models.CharField(max_length=15)
    logger = models.CharField(max_length=30)


@receiver(reversion.post_revision_commit)
def post_revision_commit(sender, **kwargs):
    """Custom post-revision hook.

    We want to track all creations and modifications of admin. objects
    (alias, mailbox, user, domain, domain alias, etc.) so we use
    django-reversion for that.

    """
    from modoboa.lib.signals import get_request

    current_user = get_request().user.username 
    logger = logging.getLogger("modoboa.admin")
    for version in kwargs["versions"]:
        if version.object is None:
            continue
        prev_revisions = reversion.get_for_object(version.object)
        if prev_revisions.count() == 1:
            action = _("added")
            level = "info"
        else:
            action = _("modified")
            level = "warning"
        message = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
            "object": unicode(version.content_type).capitalize(),
            "name": version.object_repr, "action": action,
            "user": current_user
        }
        getattr(logger, level)(message)


@receiver(post_delete)
def log_object_removal(sender, instance, **kwargs):
    """Custom post-delete hook.

    We want to know who was responsible for an object deletion.
    """
    from reversion.models import Version
    from modoboa.lib.signals import get_request

    if not reversion.is_registered(sender):
        return
    del_list = reversion.get_deleted(sender)
    try:
        version = del_list.get(object_id=instance.id)
    except Version.DoesNotExist:
        return
    logger = logging.getLogger("modoboa.admin")
    msg = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
        "object": unicode(version.content_type).capitalize(),
        "name": version.object_repr, "action": _("deleted"),
        "user": get_request().user.username
    }
    logger.critical(msg)
