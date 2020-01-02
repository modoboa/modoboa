"""Object level permissions."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from modoboa.core import constants as core_constants, signals as core_signals
from modoboa.core.models import ObjectAccess, User


def get_account_roles(user, account=None):
    """Return the list of available account roles.

    This function is used to create or modify an account.

    :param ``User`` user: connected user
    :param ``User`` account: account beeing modified (None on creation)
    :return: list of strings
    """
    result = [core_constants.SIMPLEUSERS_ROLE]
    filters = core_signals.user_can_set_role.send(
        sender="get_account_roles", user=user, role="DomainAdmins",
        account=account)
    condition = (
        user.has_perm("admin.add_domain") and
        (not filters or True in [flt[1] for flt in filters]))
    if condition:
        result += [core_constants.DOMAINADMINS_ROLE]
    if user.is_superuser:
        result += [
            core_constants.RESELLERS_ROLE, core_constants.SUPERADMINS_ROLE]
    return sorted(result, key=lambda role: role[1])


def grant_access_to_object(user, obj, is_owner=False):
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
    """
    ct = ContentType.objects.get_for_model(obj)
    entry, created = ObjectAccess.objects.get_or_create(
        user=user, content_type=ct, object_id=obj.id)
    entry.is_owner = is_owner
    entry.save()
    if not created or not is_owner:
        return
    for su in User.objects.filter(is_superuser=True):
        if su == user:
            continue
        ObjectAccess.objects.get_or_create(
            user=su, content_type=ct, object_id=obj.id
        )


def grant_access_to_objects(user, objects, ct):
    """Grant access to a collection of objects

    All objects in the collection must share the same type (ie. ``ct``
    applies to all objects).

    :param user: a ``User`` object
    :param objects: a list of objects
    :param ct: the content type
    """
    for obj in objects:
        ObjectAccess.objects.get_or_create(
            user=user, content_type=ct, object_id=obj.id)


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
            ObjectAccess.objects.get(
                content_type=ct, object_id=obj.id, is_owner=True
            )
        except ObjectAccess.DoesNotExist:
            grant_access_to_object(
                User.objects.filter(is_superuser=True)[0], obj, True
            )
    else:
        ObjectAccess.objects.filter(
            content_type=ct, object_id=obj.id
        ).delete()


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
        if group.permissions.filter(
                content_type=ct, codename=permname).exists():
            continue
        group.permissions.add(
            Permission.objects.get(content_type=ct, codename=permname)
        )
