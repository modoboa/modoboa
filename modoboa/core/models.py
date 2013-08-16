import re
import hashlib
import crypt
import base64
from random import Random
import reversion
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.crypto import constant_time_compare
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import (
    UserManager, Group, AbstractBaseUser, PermissionsMixin
)
from modoboa.lib import events, md5crypt, parameters
from modoboa.lib.exceptions import PermDeniedException
from modoboa.core.extensions import exts_pool
from modoboa.core.exceptions import AdminError

try:
    from modoboa.lib.ldaputils import *
    ldap_available = True
except ImportError:
    ldap_available = False


class User(AbstractBaseUser, PermissionsMixin):
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

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = "admin_user"
        ordering = ["username"]

    password_expr = re.compile(r'(\{(\w+)\}|(\$1\$))(.+)')

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

        # if self.has_mailbox:
        #     mb = self.mailbox_set.all()[0]
        #     if not fromuser.can_access(mb):
        #         raise PermDeniedException
        #     mb.delete(keepdir=keep_mb_dir)

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
            prefix = ""  # the result already has $1$ prepended to it
                         # to signify what this is
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
        else:
            if not ldap_available:
                raise AdminError(
                    _("Failed to update password: LDAP module not installed")
                )

            ab = LDAPAuthBackend()
            try:
                ab.update_user_password(self.username, curvalue, raw_value)
            except LDAPException, e:
                raise AdminError(_("Failed to update password: %s" % str(e)))
        events.raiseEvent(
            "PasswordUpdated", self, raw_value, self.pk is None
        )

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
        elif scheme == u"$1$":  # md5crypt
            salt, hashed = val2.split('$')
            val1 = md5crypt(raw_value, str(salt))
            val2 = self.password  # re-add scheme for comparison below
        else:
            val1 = raw_value
        return constant_time_compare(val1, val2)

    @property
    def tags(self):
        return [{"name": "account", "label": _("account"), "type": "idt"},
                {"name": self.group, "label": self.group, "type": "grp", "color": "info"}]

    # @property
    # def has_mailbox(self):
    #     return self.mailbox_set.count() != 0

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
            return "SimpleUsers"

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

reversion.register(User)


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
        if self.instance is None:
            return
        self.instance.destroy()

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
    import logging

    if kwargs["revision"].user is None:
        return
    logger = logging.getLogger("modoboa.admin")
    for version in kwargs["versions"]:
        if version.type == reversion.models.VERSION_ADD:
            action = _("added")
            level = "info"
        elif version.type == reversion.models.VERSION_CHANGE:
            action = _("modified")
            level = "warning"
        else:
            action = _("deleted")
            level = "critical"
        message = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
            "object": unicode(version.content_type).capitalize(),
            "name": version.object_repr, "action": action,
            "user": kwargs["revision"].user.username
        }
        getattr(logger, level)(message)
