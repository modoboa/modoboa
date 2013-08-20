from django.shortcuts import render
from django.db import transaction
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.views.decorators.csrf import ensure_csrf_cookie
from modoboa.lib import parameters, events
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.webutils import ajax_simple_response, _render_to_string
from modoboa.lib.formutils import CreationWizard
from modoboa.lib.templatetags.libextras import pagination_bar
from modoboa.core.models import User
from modoboa.extensions.admin.models import Mailbox
from modoboa.extensions.admin.lib import (
    get_sort_order, get_listing_page, get_identities
)
from modoboa.extensions.admin.exceptions import AdminError
from modoboa.extensions.admin.forms import (
    AccountForm, AccountFormGeneral, AccountFormMail
)


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.add_user") or u.has_perm("admin.add_alias")
)
def _identities(request):
    idents_list = get_identities(request.user, request.GET)
    sort_order, sort_dir = get_sort_order(request.GET, "identity",
                                          ["identity", "name_or_rcpt", "tags"])
    if sort_order in ["identity", "name_or_rcpt"]:
        objects = sorted(idents_list, key=lambda o: getattr(o, sort_order),
                         reverse=sort_dir == '-')
    else:
        objects = sorted(idents_list, key=lambda o: o.tags[0],
                         reverse=sort_dir == '-')
    page = get_listing_page(objects, request.GET.get("page", 1))
    return ajax_simple_response({
        "table": _render_to_string(request, "admin/identities_table.html", {
            "identities": page.object_list,
            "tableid": "objects_table"
        }),
        "handle_mailboxes": parameters.get_admin("HANDLE_MAILBOXES",
                                                 raise_error=False),
        "page": page.number,
        "paginbar": pagination_bar(page)
    })


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.add_user") or u.has_perm("admin.add_alias")
)
@ensure_csrf_cookie
def identities(request, tplname="admin/identities.html"):
    return render(request, tplname, {
        "selection": "identities",
        "deflocation": "list/"
    })


@login_required
@permission_required("admin.add_user")
def accounts_list(request):
    accs = User.objects.filter(is_superuser=False) \
        .exclude(groups__name='SimpleUsers')
    res = [a.username for a in accs.all()]
    return ajax_simple_response(res)


@login_required
@permission_required("admin.add_mailbox")
def list_quotas(request, tplname="admin/quotas.html"):
    from modoboa.lib.dbutils import db_type

    sort_order, sort_dir = get_sort_order(request.GET, "address")
    mboxes = Mailbox.objects.get_for_admin(
        request.user, request.GET.get("searchquery", None)
    )
    mboxes = mboxes.exclude(quota=0)
    if sort_order in ["address", "quota", "quota_value__bytes"]:
        mboxes = mboxes.order_by("%s%s" % (sort_dir, sort_order))
    elif sort_order == "quota_usage":
        if db_type() == "postgres":
            select = '(admin_quota.bytes::float / (CAST(admin_mailbox.quota AS BIGINT) * 1048576)) * 100'
        else:
            select = 'admin_quota.bytes / (admin_mailbox.quota * 1048576) * 100'
        mboxes = mboxes.extra(
            select={'quota_usage': select},
            where=["admin_quota.mbox_id=admin_mailbox.id"],
            tables=["admin_quota"],
            order_by=["%s%s" % (sort_dir, sort_order)]
        )
    else:
        raise AdminError(_("Invalid request"))
    page = get_listing_page(mboxes, request.GET.get("page", 1))
    return ajax_simple_response({
        "status": "ok",
        "page": page.number,
        "paginbar": pagination_bar(page),
        "table": _render_to_string(request, tplname, {
            "mboxes": page
        })
    })


@login_required
@permission_required("admin.add_user")
@transaction.commit_on_success
def newaccount(request, tplname='common/wizard_forms.html'):
    def create_account(steps):
        """Account creation callback

        Called when all creation steps have been validated.

        :param steps: the steps data
        """
        genform = steps[0]["form"]
        genform.is_valid()
        account = genform.save()
        account.post_create(request.user)

        mailform = steps[1]["form"]
        try:
            mailform.save(request.user, account)
        except AdminError:
            # A bit uggly: transaction management doesn't work very
            # well with nested functions. Need to wait for django 1.6
            # and atomicity.
            account.delete(request.user, False)
            raise

    ctx = dict(
        title=_("New account"),
        action=reverse(newaccount),
        formid="newaccount_form",
        submit_label=_("Create")
    )
    cwizard = CreationWizard(create_account)
    cwizard.add_step(AccountFormGeneral, _("General"),
                     [dict(classes="btn-inverse next", label=_("Next"))],
                     new_args=[request.user])
    cwizard.add_step(AccountFormMail, _("Mail"),
                     [dict(classes="btn-primary submit", label=_("Create")),
                      dict(classes="btn-inverse prev", label=_("Previous"))],
                     formtpl="admin/mailform.html")

    if request.method == "POST":
        retcode, data = cwizard.validate_step(request)
        if retcode == -1:
            raise AdminError(data)
        if retcode == 1:
            return ajax_simple_response(dict(
                status="ok", title=cwizard.get_title(data + 1), stepid=data
            ))
        if retcode == 2:
            return ajax_simple_response(dict(
                status="ok", respmsg=_("Account created")
            ))

        from modoboa.lib.templatetags.libextras import render_form
        return ajax_simple_response(dict(
            status="ko", stepid=data,
            form=render_form(cwizard.steps[data]["form"])
        ))

    cwizard.create_forms()
    ctx.update(steps=cwizard.steps)
    ctx.update(subtitle="1. %s" % cwizard.steps[0]['title'])
    return render(request, tplname, ctx)


@login_required
@permission_required("admin.change_user")
@transaction.commit_on_success
def editaccount(request, accountid, tplname="common/tabforms.html"):
    account = User.objects.get(pk=accountid)
    if not request.user.can_access(account):
        raise PermDeniedException
    mb = None
    if account.mailbox_set.count():
        mb = account.mailbox_set.all()[0]

    instances = dict(general=account, mail=mb, perms=account)
    events.raiseEvent("FillAccountInstances", request.user, account, instances)

    ctx = dict(
        title=account.username,
        formid="accountform",
        action=reverse(editaccount, args=[accountid]),
        action_label=_("Update"),
        action_classes="submit"
    )

    if request.method == "POST":
        classes = {}
        form = AccountForm(request.user, request.POST,
                           instances=instances, classes=classes)
        account.oldgroup = account.group
        if form.is_valid(mandatory_only=True):
            form.save_general_form()
            if form.is_valid(optional_only=True):
                events.raiseEvent("AccountModified", account, form.account)
                form.save()
                return ajax_simple_response(
                    dict(status="ok", respmsg=_("Account updated"))
                )
            transaction.rollback()

        ctx["tabs"] = form
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["tabs"] = AccountForm(request.user, instances=instances)
    active_tab_id = request.GET.get("active_tab", "default")
    if active_tab_id != "default":
        ctx["tabs"].active_id = active_tab_id
    return render(request, tplname, ctx)


@login_required
@permission_required("admin.delete_user")
@transaction.commit_on_success
def delaccount(request, accountid):
    keepdir = True if request.POST.get("keepdir", "false") == "true" else False

    User.objects.get(pk=accountid).delete(request.user, keepdir)

    msg = ungettext("Account deleted", "Accounts deleted", 1)
    return ajax_simple_response({"status": "ok", "respmsg": msg})


@login_required
@permission_required("admin.add_domain")
def remove_permission(request):
    domid = request.GET.get("domid", None)
    daid = request.GET.get("daid", None)
    if domid is None or daid is None:
        raise AdminError(_("Invalid request"))
    try:
        account = User.objects.get(pk=daid)
        domain = Domain.objects.get(pk=domid)
    except (User.DoesNotExist, Domain.DoesNotExist):
        raise AdminError(_("Invalid request"))
    if not request.user.can_access(account) or not request.user.can_access(domain):
        raise PermDeniedException
    domain.remove_admin(account)
    return ajax_simple_response({"status": "ok"})
