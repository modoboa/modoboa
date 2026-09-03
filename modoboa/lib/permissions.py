"""Object level permissions."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from rest_framework import permissions, serializers

from modoboa.core import constants as core_constants, signals as core_signals
from modoboa.core.models import ObjectAccess, User


def check_mailbox_ownership(user, mailbox):
    """Check that user is allowed to manipulate the given mailbox.

    :param user: a ``User`` instance (the current request user)
    :param mailbox: a ``Mailbox`` instance
    :raises serializers.ValidationError: if user has no ownership
    """
    from modoboa.admin import models as admin_models

    role = user.role
    if role == "SimpleUsers" and user.mailbox != mailbox:
        raise serializers.ValidationError(_("You don't have ownership on this mailbox"))
    elif role in ["DomainAdmins", "Resellers"]:
        mailboxes = admin_models.Mailbox.objects.get_for_admin(user)
        if mailbox not in mailboxes:
            raise serializers.ValidationError(
                _("You don't have ownership on this mailbox")
            )


def get_account_roles(user, account=None):
    """Return the list of available account roles.

    This function is used to create or modify an account.

    :param ``User`` user: connected user
    :param ``User`` account: account beeing modified (None on creation)
    :return: list of strings
    """
    if account and user == account:
        # Special case to ensure a user cannot change its own role
        return [(user.role, "")]
    result = [core_constants.SIMPLEUSERS_ROLE]
    filters = core_signals.user_can_set_role.send(
        sender="get_account_roles", user=user, role="DomainAdmins", account=account
    )
    condition = user.has_perm("admin.add_domain") and (
        not filters or True in [flt[1] for flt in filters]
    )
    if condition:
        result += [core_constants.DOMAINADMINS_ROLE]
    if user.is_superuser:
        result += [core_constants.RESELLERS_ROLE, core_constants.SUPERADMINS_ROLE]
    return sorted(result, key=lambda role: role[1])


def grant_access_to_object(user, obj, is_owner=False, superusers=None):
    """Grant access to an object for a given user

    There are two different cases where we want to grant access to an
    object for a specific user:

    * He is the owner (he's just created the object)
    * He is going to administrate the object (but he is not the owner)

    If the user is the owner, we also grant access to this object to
    all super users.

    :param user: a ``User`` object
    :param obj: an admin. object (Domain, Mailbox, ...)
    :param is_owner: the user is the unique object's owner
    :param superusers: pre-fetched super users, to avoid querying them
                       again on each call when granting access in bulk
    """
    ct = ContentType.objects.get_for_model(obj)
    entry, created = ObjectAccess.objects.get_or_create(
        user=user, content_type=ct, object_id=obj.id, defaults={"is_owner": is_owner}
    )
    if entry.is_owner != is_owner:
        entry.is_owner = is_owner
        entry.save(update_fields=["is_owner"])
    if not created or not is_owner:
        return
    if superusers is None:
        superusers = User.objects.filter(is_superuser=True)
    ObjectAccess.objects.bulk_create(
        [
            ObjectAccess(user=su, content_type=ct, object_id=obj.id)
            for su in superusers
            if su != user
        ],
        ignore_conflicts=True,
    )


def grant_access_to_objects(user, objects, ct):
    """Grant access to a collection of objects

    All objects in the collection must share the same type (ie. ``ct``
    applies to all objects).

    :param user: a ``User`` object
    :param objects: a list of objects or a ``QuerySet``
    :param ct: the content type
    """
    if isinstance(objects, QuerySet):
        # Only primary keys are needed: don't build model instances, some
        # of them query the database on their own to initialize.
        object_ids = objects.values_list("pk", flat=True)
    else:
        object_ids = (obj.id for obj in objects)
    granted = set(
        ObjectAccess.objects.filter(user=user, content_type=ct).values_list(
            "object_id", flat=True
        )
    )
    ObjectAccess.objects.bulk_create(
        [
            ObjectAccess(user=user, content_type=ct, object_id=object_id)
            for object_id in object_ids
            if object_id not in granted
        ],
        batch_size=1000,
        ignore_conflicts=True,
    )


def ungrant_access_to_object(obj, user=None):
    """Ungrant access to an object for a specific user

    If no user is provided, all entries referencing this object are
    deleted from the database.

    If a user is provided, we only remove his access. If it was the
    owner, we give the ownership to the first super admin we find.

    :param obj: an object inheriting from ``models.Model``
    :param user: a ``User`` object
    """
    ct = ContentType.objects.get_for_model(obj)
    if user is not None:
        try:
            ObjectAccess.objects.get(
                user=user, content_type=ct, object_id=obj.id
            ).delete()
        except ObjectAccess.DoesNotExist:
            pass
        try:
            ObjectAccess.objects.get(content_type=ct, object_id=obj.id, is_owner=True)
        except ObjectAccess.DoesNotExist:
            grant_access_to_object(User.objects.filter(is_superuser=True)[0], obj, True)
    else:
        ObjectAccess.objects.filter(content_type=ct, object_id=obj.id).delete()


def ungrant_access_to_objects(objects):
    """Cancel all accesses for a given object list.

    :param objects: a list of objects inheriting from ``models.Model``
    """
    for obj in objects:
        ct = ContentType.objects.get_for_model(obj)
        ObjectAccess.objects.filter(content_type=ct, object_id=obj.id).delete()


def get_object_owner(obj):
    """Return the unique owner of this object

    :param obj: an object inheriting from ``model.Model``
    :return: a ``User`` object
    """
    ct = ContentType.objects.get_for_model(obj)
    try:
        entry = ObjectAccess.objects.get(
            content_type=ct, object_id=obj.id, is_owner=True
        )
    except ObjectAccess.DoesNotExist:
        return None
    return entry.user


def add_permissions_to_group(group, permissions):
    """Add the specified permissions to a django group."""
    if isinstance(group, str):
        group = Group.objects.get(name=group)

    for appname, modelname, permname in permissions:
        ct = ContentType.objects.get_by_natural_key(appname, modelname)
        if group.permissions.filter(content_type=ct, codename=permname).exists():
            continue
        group.permissions.add(
            Permission.objects.get(content_type=ct, codename=permname)
        )


class IsSuperUser(permissions.BasePermission):
    """Permission class to allow only super users."""

    def has_permission(self, request, view):
        return request.user.is_superuser


class IsPrivilegedUser(permissions.BasePermission):
    """Permission class to allow any privileged user."""

    def has_permission(self, request, view):
        return request.user.role != core_constants.SIMPLEUSERS_ROLE[0]


class CanCreateDomain(permissions.BasePermission):
    """Permissions class to allow users with add_domain right."""

    def has_permission(self, request, view):
        return request.user.has_perm("admin.add_domain")


class CanViewDomain(permissions.BasePermission):
    """Permissions class to allow users with view_domain right."""

    def has_permission(self, request, view):
        return request.user.has_perm("admin.view_domain")


class CanDeleteDomain(permissions.BasePermission):
    """Permissions class to allow users with delete_domain right."""

    def has_permission(self, request, view):
        return request.user.has_perm("admin.delete_domain")
