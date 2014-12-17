# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters, events
from modoboa.lib.exceptions import PermDeniedException, BadRequest, Conflict
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions.admin.models import (
    Domain, DomainAlias, Mailbox, Alias
)

admin_events = [
    "DomainCreated",
    "DomainModified",
    "DomainDeleted",
    "DomainOwnershipRemoved",
    "ExtraDomainEntries",
    "ExtraDomainMenuEntries",
    "ExtraDomainFilters",
    "GetDomainActions",
    "GetDomainModifyLink",
    "CheckDomainName",

    "DomainAliasCreated",
    "DomainAliasDeleted",

    "MailboxCreated",
    "MailboxDeleted",
    "MailboxModified",

    "MailboxAliasCreated",
    "MailboxAliasDeleted",

    "ExtraDomainForm",
    "FillDomainInstances",

    "ExtraAccountForm",
    "CheckExtraAccountForm",
    "FillAccountInstances",

    "ExtraDomainImportHelp",
    "ImportObject"
]


class AdminConsole(ModoExtension):
    name = "admin"
    label = ugettext_lazy("Administration console")
    version = "1.0"
    description = ugettext_lazy(
        "Web based console to manage domains, accounts and aliases"
    )
    always_active = True

    def load(self):
        from modoboa.extensions.admin.app_settings import AdminParametersForm
        parameters.register(AdminParametersForm, ugettext_lazy("Administration"))
        events.declare(admin_events)

    def destroy(self):
        parameters.unregister()

exts_pool.register_extension(AdminConsole, show=False)


@events.observe("ExtraUprefsRoutes")
def extra_routes():
    from django.conf.urls import url
    return [
        url(r'^user/forward/',
            'modoboa.extensions.admin.views.user.forward',
            name="user_forward"),
    ]


@events.observe("AdminMenuDisplay")
def admin_menu(target, user):
    if target != "top_menu":
        return []
    entries = []
    if user.has_perm("admin.view_domains"):
        entries += [
            {"name" : "domains",
             "url" : reverse("admin:domain_list"),
             "label" : _("Domains")}
        ]
    if user.has_perm("core.add_user") or user.has_perm("admin.add_alias"):
        entries += [
            {"name" : "identities",
             "url" : reverse("admin:identity_list"),
             "label" : _("Identities")},
        ]
    return entries


@events.observe("UserMenuDisplay")
def user_menu(target, user):
    if target != "uprefs_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "forward",
         "class": "ajaxnav",
         "url": "forward/",
         "label": ugettext_lazy("Forward")}
    ]


@events.observe("RoleChanged")
def grant_access_to_all_objects(user, role):
    from django.contrib.contenttypes.models import ContentType
    from modoboa.lib.permissions import grant_access_to_objects
    from modoboa.core.models import User

    if role != "SuperAdmins":
        return
    grant_access_to_objects(
        user, User.objects.all(),
        ContentType.objects.get_for_model(User)
    )
    grant_access_to_objects(
        user, Domain.objects.all(),
        ContentType.objects.get_for_model(Domain)
    )
    grant_access_to_objects(
        user, DomainAlias.objects.all(),
        ContentType.objects.get_for_model(DomainAlias)
    )
    grant_access_to_objects(
        user, Mailbox.objects.all(),
        ContentType.objects.get_for_model(Mailbox)
    )
    grant_access_to_objects(
        user, Alias.objects.all(),
        ContentType.objects.get_for_model(Alias)
    )


@events.observe("AccountExported")
def export_admin_domains(admin):
    result = [admin.mailbox_set.all()[0].quota] \
        if admin.mailbox_set.count() else ['']
    if admin.group != "DomainAdmins":
        return result
    return result + [dom.name for dom in Domain.objects.get_for_admin(admin)]


@events.observe("AccountImported")
def import_account_mailbox(user, account, row):
    """Handle extra fields when an account is imported.

    Expected fields:

    email address; quota; [domain; ...]

    :param User user: user importing the account
    :param User account: account being imported
    :param list rom: list of fields (strings)
    """
    account.email = row[0].strip()
    if account.email:
        account.save()
        mailbox, domname = split_mailbox(account.email)
        try:
            domain = Domain.objects.get(name=domname)
        except Domain.DoesNotExist:
            raise BadRequest(
                _("Account import failed (%s): domain does not exist" % account.username)
            )
        if not user.can_access(domain):
            raise PermDeniedException
        try:
            mb = Mailbox.objects.get(address=mailbox, domain=domain)
        except Mailbox.DoesNotExist:
            pass
        else:
            raise  Conflict(_("Mailbox %s already exists" % account.email))
        if len(row) == 1:
            quota = None
        else:
            try:
                quota = int(row[1].strip())
            except ValueError:
                raise BadRequest(
                    _("Account import failed (%s): wrong quota value" % account.username)
                )
        use_domain_quota = True if not quota else False
        mb = Mailbox(address=mailbox, domain=domain,
                     user=account, use_domain_quota=use_domain_quota)
        mb.set_quota(quota, override_rules=user.has_perm("admin.change_domain"))
        mb.save(creator=user)
    if account.group == "DomainAdmins":
        for domname in row[2:]:
            try:
                dom = Domain.objects.get(name=domname.strip())
            except Domain.DoesNotExist:
                continue
            dom.add_admin(account)


@events.observe("AccountAutoCreated")
def account_auto_created(user):
    from modoboa.core.models import User
    from modoboa.extensions.admin.lib import check_if_domain_exists
    from modoboa.lib.permissions import grant_access_to_object

    if parameters.get_admin("AUTO_CREATE_DOMAIN_AND_MAILBOX") == "no":
        return
    localpart, domname = split_mailbox(user.username)
    if user.group != 'SimpleUsers' and domname is None:
        return
    sadmins = User.objects.filter(is_superuser=True)
    try:
        domain = Domain.objects.get(name=domname)
    except Domain.DoesNotExist:
        label = check_if_domain_exists(
            domname, [(DomainAlias, _('domain alias'))])
        if label is not None:
            return
        domain = Domain(name=domname, enabled=True, quota=0)
        domain.save(creator=sadmins[0])
        for su in sadmins[1:]:
            grant_access_to_object(su, domain)
    try:
        mb = Mailbox.objects.get(domain=domain, address=localpart)
    except Mailbox.DoesNotExist:
        mb = Mailbox(
            address=localpart, domain=domain, user=user, use_domain_quota=True
        )
        mb.set_quota(override_rules=True)
        mb.save(creator=sadmins[0])
        for su in sadmins[1:]:
            grant_access_to_object(su, mb)


@events.observe("UserLogin")
def user_logged_in(request, username, password):
    from modoboa.lib.cryptutils import encrypt

    if request.user.mailbox_set.count():
        request.session["password"] = encrypt(password)


@events.observe("AccountDeleted")
def account_deleted(account, byuser, **kwargs):
    """'AccountDeleted' listener.

    When an account is deleted, we also need to remove its mailbox (if
    any).
    """
    if not account.mailbox_set.count():
        return
    mb = account.mailbox_set.all()[0]
    if not byuser.can_access(mb):
        raise PermDeniedException
    keep_mb_dir = kwargs.get("keep_mb_dir", True)
    mb.delete(keepdir=keep_mb_dir)
