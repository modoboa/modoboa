"""Rights of users on Radicale collections.

They are requested by the radicale-modoboa-rights plugin, which decides
locally the access of users to their own calendars and to the shared
calendars of their domain. Shares are also written to the rights file
(generate_rights command), so both give the same access.
"""

from django.db.models import Q

from modoboa.admin.models import Domain
from modoboa.core.models import User
from modoboa.parameters import tools as param_tools

from . import models

#: Matches any domain in administered and managed domains
ALL_DOMAINS = "*"


def get_administered_domains(user):
    """Return the names of the domains administered by user."""
    if user.is_superuser:
        return [ALL_DOMAINS]
    return sorted(
        Domain.objects.get_for_admin(user).values_list("name", flat=True).distinct()
    )


def get_effective_access_rules():
    """Return the access rules granting an access.

    Rules granting no access, or involving an inactive owner or grantee,
    or a calendar of a disabled domain, are ignored.
    """
    return models.AccessRule.objects.filter(
        Q(read=True) | Q(write=True),
        mailbox__user__is_active=True,
        calendar__mailbox__user__is_active=True,
        calendar__mailbox__domain__enabled=True,
    )


def get_share_permissions(read, write):
    """Return Radicale permissions matching an access rule."""
    permissions = "r" if read else ""
    if write:
        # 'd' forbids the deletion of the calendar itself
        permissions += "wd"
    return permissions


def get_user_rights(username):
    """Return the rights of username on collections owned by someone else.

    admin_domains: domains whose user calendars the user administers
    managed_domains: domains whose shared calendars the user manages
    shares: user calendars shared with the user (path -> permissions)
    """
    rights = {"admin_domains": [], "managed_domains": [], "shares": {}}
    user = User.objects.filter(username=username, is_active=True).first()
    if user is None:
        return rights
    domains = get_administered_domains(user)
    rights["managed_domains"] = domains
    if param_tools.get_global_parameter(
        "allow_calendars_administration", app="calendars"
    ):
        rights["admin_domains"] = domains
    rules = (
        get_effective_access_rules()
        .filter(mailbox__user=user)
        .order_by("pk")
        .values_list("calendar___path", "read", "write")
    )
    rights["shares"] = {
        path: get_share_permissions(read, write) for path, read, write in rules
    }
    return rights
