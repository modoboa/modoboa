import reversion
from django.shortcuts import render
from django.db import transaction
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.views.decorators.csrf import ensure_csrf_cookie
from modoboa.lib import parameters, events
from modoboa.lib.exceptions import (
    PermDeniedException, BadRequest
)
from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)
from modoboa.lib.formutils import CreationWizard
from modoboa.lib.templatetags.lib_tags import pagination_bar
from modoboa.core.models import User
from modoboa.extensions.admin.models import Mailbox, Domain
from modoboa.extensions.admin.lib import (
    get_sort_order, get_listing_page, get_identities
)
from modoboa.extensions.admin.forms import (
    AccountForm, AccountFormGeneral, AccountFormMail
)


@login_required
@user_passes_test(
    lambda u: u.has_perm("core.add_user") or u.has_perm("admin.add_alias")
)
def _identities(request):
    filters = dict((fname, request.GET.get(fname, None))
                   for fname in ['searchquery', 'idtfilter', 'grpfilter'])
    request.session['identities_filters'] = filters
    idents_list = get_identities(request.user, **filters)
    sort_order, sort_dir = get_sort_order(request.GET, "identity",
                                          ["identity", "name_or_rcpt", "tags"])
    if sort_order in ["identity", "name_or_rcpt"]:
        objects = sorted(idents_list, key=lambda o: getattr(o, sort_order),
                         reverse=sort_dir == '-')
    else:
        objects = sorted(idents_list, key=lambda o: o.tags[0],
                         reverse=sort_dir == '-')
    page = get_listing_page(objects, request.GET.get("page", 1))
    return render_to_json_response({
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
@permission_required("core.add_user")
def accounts_list(request):
    accs = User.objects.filter(is_superuser=False) \
        .exclude(groups__name='SimpleUsers')
    res = [a.username for a in accs.all()]
    return render_to_json_response(res)


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
        raise BadRequest(_("Invalid request"))
    page = get_listing_page(mboxes, request.GET.get("page", 1))
    return render_to_json_response({
        "page": page.number,
        "paginbar": pagination_bar(page),
        "table": _render_to_string(request, tplname, {
            "mboxes": page
        })
    })


@login_required
@permission_required("core.add_user")
@transaction.commit_on_success
@reversion.create_revision()
def newaccount(request, tplname='common/wizard_forms.html'):
    """Create a new account.

    .. note:: An issue still remains int this code: if all validation
       steps are successful but an error occurs after we call 'save',
       the account will be created. It happens transaction management
       doesn't work very well with nested functions. Need to wait for
       django 1.6 and atomicity.
    """
    cwizard = CreationWizard()
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
            raise BadRequest(data)
        if retcode == 1:
            return render_to_json_response(
                {'title': cwizard.get_title(data + 1), 'stepid': data}
            )
        if retcode == 2:
            genform = cwizard.steps[0]["form"]
            account = genform.save()
            account.post_create(request.user)
            mailform = cwizard.steps[1]["form"]
            mailform.save(request.user, account)
            return render_to_json_response(_("Account created"))
        return render_to_json_response({
            'stepid': data, 'form_errors': cwizard.errors
        }, status=400)

    ctx = {
        'title': _("New account"),
        'action': reverse(newaccount),
        'formid': 'newaccount_form',
        'submit_label': _("Create")
    }
    cwizard.create_forms()
    ctx.update(steps=cwizard.steps)
    ctx.update(subtitle="1. %s" % cwizard.steps[0]['title'])
    return render(request, tplname, ctx)


@login_required
@permission_required("core.change_user")
@transaction.commit_on_success
@reversion.create_revision()
def editaccount(request, accountid, tplname="common/tabforms.html"):
    account = User.objects.get(pk=accountid)
    if not request.user.can_access(account):
        raise PermDeniedException
    mb = None
    if account.mailbox_set.count():
        mb = account.mailbox_set.all()[0]

    instances = dict(general=account, mail=mb, perms=account)
    events.raiseEvent("FillAccountInstances", request.user, account, instances)

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
                return render_to_json_response(_("Account updated"))
        return render_to_json_response({'form_errors': form.errors}, status=400)

    ctx = {
        'title': account.username,
        'formid': 'accountform',
        'action': reverse(editaccount, args=[accountid]),
        'action_label': _('Update'),
        'action_classes': 'submit',
        'tabs': AccountForm(request.user, instances=instances)
    }
    active_tab_id = request.GET.get("active_tab", "default")
    if active_tab_id != "default":
        ctx["tabs"].active_id = active_tab_id
    return render(request, tplname, ctx)


@login_required
@permission_required("core.delete_user")
@transaction.commit_on_success
def delaccount(request, accountid):
    keepdir = True if request.POST.get("keepdir", "false") == "true" else False
    User.objects.get(pk=accountid).delete(request.user, keep_mb_dir=keepdir)
    return render_to_json_response(
        ungettext("Account deleted", "Accounts deleted", 1)
    )


@login_required
@permission_required("admin.add_domain")
def remove_permission(request):
    domid = request.GET.get("domid", None)
    daid = request.GET.get("daid", None)
    if domid is None or daid is None:
        raise BadRequest(_("Invalid request"))
    try:
        account = User.objects.get(pk=daid)
        domain = Domain.objects.get(pk=domid)
    except (User.DoesNotExist, Domain.DoesNotExist):
        raise BadRequest(_("Invalid request"))
    if not request.user.can_access(account) or not request.user.can_access(domain):
        raise PermDeniedException
    domain.remove_admin(account)
    return render_to_json_response({})
