# -*- coding: utf-8 -*-

"""Core models."""

from __future__ import unicode_literals

import re
from email.header import Header

import jsonfield
from reversion import revisions as reversion

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.encoding import (
    force_str, python_2_unicode_compatible, smart_bytes, smart_text
)
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.core.password_hashers import get_password_hasher
from modoboa.lib.exceptions import (
    BadRequest, Conflict, InternalError, PermDeniedException
)
from modoboa.parameters import tools as param_tools
from . import constants, signals

try:
    from modoboa.lib.ldap_utils import LDAPAuthBackend
    ldap_available = True
except ImportError:
    ldap_available = False


@python_2_unicode_compatible
class User(AbstractUser):

    """Custom User model.

    It overloads the way passwords are stored into the database. The
    main reason to change this mechanism is to ensure the
    compatibility with the way Dovecot stores passwords.

    It also adds new attributes and methods.
    """

    username = models.CharField(max_length=254, unique=True)
    email = models.EmailField(max_length=254, blank=True, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_local = models.BooleanField(default=True, db_index=True)
    master_user = models.BooleanField(
        ugettext_lazy("Allow mailboxes access"), default=False,
        help_text=ugettext_lazy(
            "Allow this administrator to access user mailboxes"
        )
    )
    password = models.CharField(ugettext_lazy("password"), max_length=256)

    language = models.CharField(
        ugettext_lazy("language"),
        max_length=10, default="en", choices=constants.LANGUAGES,
        help_text=ugettext_lazy(
            "Prefered language to display pages."
        )
    )
    phone_number = models.CharField(
        ugettext_lazy("Phone number"), max_length=128, blank=True, null=True)
    secondary_email = models.EmailField(
        ugettext_lazy("Secondary email"), max_length=254,
        blank=True, null=True,
        help_text=ugettext_lazy(
            "An alternative e-mail address, can be used for recovery needs.")
    )
    _parameters = jsonfield.JSONField(default={})

    class Meta(object):
        ordering = ["username"]
        index_together = [
            ["email", "is_active"]
        ]

    password_expr = re.compile(r'\{([\w\-]+)\}(.+)')

    def __init__(self, *args, **kwargs):
        """Load parameter manager."""
        super(User, self).__init__(*args, **kwargs)
        self.parameters = param_tools.Manager("user", self._parameters)

    def _crypt_password(self, raw_value):
        """Crypt the local password using the appropriate scheme.

        In case we don't find the scheme (for example when the
        management framework is used), we load the parameters and try
        one more time.

        """
        scheme = param_tools.get_global_parameter(
            "password_scheme", raise_exception=False)
        if scheme is None:
            from modoboa.core.apps import load_core_settings
            load_core_settings()
            scheme = param_tools.get_global_parameter(
                "password_scheme", raise_exception=False)
        raw_value = smart_bytes(raw_value)
        return get_password_hasher(scheme.upper())().encrypt(raw_value)

    def set_password(self, raw_value, curvalue=None):
        """Password update

        Update the current mailbox's password with the given clear
        value. This value is encrypted according to the defined method
        before it is saved.

        :param raw_value: the new password's value
        :param curvalue: the current password (for LDAP authentication)
        """
        ldap_sync_enable = param_tools.get_global_parameter("ldap_enable_sync")
        if self.is_local or ldap_sync_enable:
            self.password = self._crypt_password(raw_value)
        else:
            if not ldap_available:
                raise InternalError(
                    _("Failed to update password: LDAP module not installed")
                )
            LDAPAuthBackend().update_user_password(
                self.username, curvalue, raw_value
            )
        signals.account_password_updated.send(
            sender=self.__class__,
            account=self, password=raw_value, created=self.pk is None)

    def check_password(self, raw_value):
        """Compare raw_value to current password."""
        match = self.password_expr.match(self.password)
        if match is None:
            return False
        raw_value = force_str(raw_value)
        scheme = match.group(1)
        val2 = match.group(2)
        hasher = get_password_hasher(scheme)
        return hasher().verify(raw_value, val2)

    def __str__(self):
        return smart_text(self.get_username())

    def get_absolute_url(self):
        """Return detail url for this user."""
        return reverse("admin:account_detail", args=[self.pk])

    @property
    def tags(self):
        return [{"name": "account", "label": _("account"), "type": "idt"},
                {"name": self.role, "label": self.role,
                 "type": "grp", "color": "info"}]

    @property
    def fullname(self):
        result = self.username
        if self.first_name != "":
            result = self.first_name
        if self.last_name != "":
            if result != "":
                result += " "
            result += self.last_name
        return result

    @property
    def identity(self):
        return self.username

    @property
    def name_or_rcpt(self):
        if self.first_name != "":
            return "%s %s" % (self.first_name, self.last_name)
        return "----"

    @property
    def enabled(self):
        return self.is_active

    @property
    def encoded_address(self):
        if self.first_name != "" or self.last_name != "":
            return '"{}" <{}>'.format(
                Header(self.fullname, "utf8").encode(), self.email)
        return self.email

    def is_owner(self, obj):
        """Tell is the user is the unique owner of this object

        :param obj: an object inheriting from ``models.Model``
        :return: a boolean
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            ooentry = self.objectaccess_set.get(
                content_type=ct, object_id=obj.id)
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
            ooentry = self.objectaccess_set.get(
                content_type=ct, object_id=obj.id)
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

    @property
    def role(self):
        """Return user role."""
        if not hasattr(self, "_role"):
            if self.is_superuser:
                self._role = "SuperAdmins"
            else:
                try:
                    self._role = self.groups.all()[0].name
                except IndexError:
                    self._role = "---"
        return self._role

    @role.setter
    def role(self, role):
        """Set administrative role for this account

        :param string role: the role to set
        """
        if role is None or self.role == role:
            return
        signals.account_role_changed.send(
            sender=self.__class__, account=self, role=role)
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
            if role != "SimpleUsers" and not self.can_access(self):
                from modoboa.lib.permissions import grant_access_to_object
                grant_access_to_object(self, self)
        self.save()
        self._role = role

    def get_role_display(self):
        """Return the display name of this role."""
        for role in constants.ROLES:
            if role[0] == self.role:
                return role[1]
        return _("Unknown")

    @cached_property
    def is_admin(self):
        """Shortcut to check if user is administrator."""
        return self.role in constants.ADMIN_GROUPS

    def post_create(self, creator):
        """Grant permission on this user to creator."""
        from modoboa.lib.permissions import grant_access_to_object
        grant_access_to_object(creator, self, is_owner=True)

    def save(self, *args, **kwargs):
        creator = kwargs.pop("creator", None)
        super(User, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def from_csv(self, user, row, crypt_password=True):
        """Create a new account from a CSV file entry.

        The expected order is the following::

        "account", loginname, password, first name, last name, enabled, role

        Additional fields can be added using the *account_imported* signal.

        :param user: a ``core.User`` instance
        :param row: a list containing the expected information
        :param crypt_password:
        """
        from modoboa.lib.permissions import get_account_roles

        if len(row) < 7:
            raise BadRequest(_("Invalid line"))

        desired_role = row[6].strip()
        if not user.is_superuser:
            allowed_roles = get_account_roles(user)
            allowed_roles = [role[0] for role in allowed_roles]
            if desired_role not in allowed_roles:
                raise PermDeniedException(_(
                    "You can't import an account with a role greater than "
                    "yours"
                ))

        self.username = row[1].strip().lower()
        try:
            User.objects.get(username=self.username)
        except User.DoesNotExist:
            pass
        else:
            raise Conflict

        if desired_role == "SimpleUsers":
            if len(row) < 8 or not row[7].strip():
                raise BadRequest(
                    _("The simple user '%s' must have a valid email address"
                      % self.username)
                )
            if self.username != row[7].strip():
                raise BadRequest(
                    _("username and email fields must not differ for '%s'"
                      % self.username)
                )

        if crypt_password:
            self.set_password(row[2].strip())
        else:
            self.password = row[2].strip()
        self.first_name = row[3].strip()
        self.last_name = row[4].strip()
        self.is_active = (row[5].strip().lower() in ["true", "1", "yes", "y"])
        self.language = settings.LANGUAGE_CODE
        self.save()
        self.role = desired_role
        self.post_create(user)
        if len(row) < 8:
            return
        signals.account_imported.send(
            sender=self.__class__, user=user, account=self, row=row[7:])

    def to_csv(self, csvwriter):
        """Export this account.

        The CSV format is used to export.

        :param csvwriter: csv object
        """
        row = [
            "account",
            smart_text(self.username),
            smart_text(self.password),
            smart_text(self.first_name),
            smart_text(self.last_name),
            smart_text(self.is_active),
            smart_text(self.role),
            smart_text(self.email)
        ]
        results = signals.account_exported.send(
            sender=self.__class__, user=self)
        for result in results:
            row += result[1]
        csvwriter.writerow(row)


reversion.register(User)


def populate_callback(user, group="SimpleUsers"):
    """Populate callback

    If the LDAP authentication backend is in use, this callback will
    be called each time a new user authenticates succesfuly to
    Modoboa. This function is in charge of creating the mailbox
    associated to the provided ``User`` object.

    :param user: a ``User`` instance
    """
    from modoboa.lib.permissions import grant_access_to_object

    sadmins = User.objects.filter(is_superuser=True)
    user.role = group
    user.post_create(sadmins[0])
    for su in sadmins[1:]:
        grant_access_to_object(su, user)
    signals.account_auto_created.send(
        sender="populate_callback", user=user)


@python_2_unicode_compatible
class ObjectAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    is_owner = models.BooleanField(default=False)

    class Meta(object):
        unique_together = (("user", "content_type", "object_id"),)

    def __str__(self):
        return "%s => %s (%s)" % (
            self.user, self.content_object, self.content_type
        )


class Log(models.Model):
    """Simple log in database."""

    date_created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    level = models.CharField(max_length=15)
    logger = models.CharField(max_length=30)


class LocalConfig(models.Model):
    """Store instance configuration here."""

    api_pk = models.PositiveIntegerField(null=True)
    site = models.ForeignKey("sites.Site", on_delete=models.CASCADE)

    # API results cache
    api_versions = jsonfield.JSONField()

    _parameters = jsonfield.JSONField(default={})

    def __init__(self, *args, **kwargs):
        """Load parameter manager."""
        super(LocalConfig, self).__init__(*args, **kwargs)
        self.parameters = param_tools.Manager("global", self._parameters)
