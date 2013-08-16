from django.db import transaction, IntegrityError
from django.utils.translation import ugettext as _, ungettext
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from modoboa.lib import events
from modoboa.lib.webutils import ajax_response, ajax_simple_response
from modoboa.lib.exceptions import PermDeniedException
from modoboa.extensions.admin.exceptions import AdminError
from modoboa.extensions.admin.forms import AliasForm
from modoboa.extensions.admin.models import Alias


def _validate_alias(request, form, successmsg, tplname, commonctx, callback=None):
    """Alias validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        form.set_recipients()
        try:
            alias = form.save()
        except IntegrityError:
            raise AdminError(_("Alias with this name already exists"))
        if callback:
            callback(request.user, alias)
        return ajax_simple_response({"status": "ok", "respmsg": successmsg})

    if "targets" in request.POST:
        targets = request.POST.getlist("targets")
        commonctx["targets"] = targets[:-1]

    commonctx["form"] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)


def _new_alias(request, title, action, successmsg,
               tplname="common/generic_modal_form.html"):
    events.raiseEvent("CanCreate", request.user, "mailbox_aliases")
    ctx = {
        "title": title,
        "action": action,
        "formid": "aliasform",
        "action_label": _("Create"),
        "action_classes": "submit"
    }
    if request.method == "POST":
        def callback(user, alias):
            alias.post_create(user)

        form = AliasForm(request.user, request.POST)
        return _validate_alias(
            request, form, successmsg, tplname, ctx, callback
        )

    form = AliasForm(request.user)
    ctx["form"] = form
    return render(request, tplname, ctx)


@login_required
@user_passes_test(lambda u: u.has_perm("admin.add_user")
                  or u.has_perm("admin.add_alias"))
def allowed_recipients_list(request):
    ret = [mb.full_address for mb in request.user.get_mailboxes()]
    ret += [al.full_address for al in request.user.get_aliases()]
    return ajax_simple_response(ret)


@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newdlist(request):
    return _new_alias(
        request, _("New distribution list"), reverse(newdlist),
        _("Distribution list created")
    )


@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newalias(request):
    return _new_alias(
        request, _("New alias"), reverse(newalias),
        _("Alias created")
    )


@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newforward(request):
    return _new_alias(
        request, _("New forward"), reverse(newforward),
        _("Forward created")
    )


@login_required
@permission_required("admin.change_alias")
def editalias(request, alid, tplname="common/generic_modal_form.html"):
    alias = Alias.objects.get(pk=alid)
    if not request.user.can_access(alias):
        raise PermDeniedException
    ctx = dict(
        action=reverse(editalias, args=[alias.id]),
        formid="aliasform",
        title=alias.full_address,
        action_label=_("Update"),
        action_classes="submit"
    )
    if len(alias.get_recipients()) >= 2:
        successmsg = _("Distribution list modified")
    elif alias.extmboxes != "":
        successmsg = _("Forward modified")
    else:
        successmsg = _("Alias modified")
    if request.method == "POST":
        form = AliasForm(request.user, request.POST, instance=alias)
        return _validate_alias(request, form, successmsg, tplname, ctx)

    form = AliasForm(request.user, instance=alias)
    ctx["form"] = form
    return render(request, tplname, ctx)


def _del_alias(request, msg, msgs):
    selection = request.GET["selection"].split(",")
    for alid in selection:
        alias = Alias.objects.get(pk=alid)
        if not request.user.can_access(alias):
            raise PermDeniedException
        alias.delete()

    msg = ungettext(msg, msgs, len(selection))
    return ajax_simple_response({"status": "ok", "respmsg": msg})


@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def delalias(request):
    return _del_alias(request, "Alias deleted", "Aliases deleted")


@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def deldlist(request):
    return _del_alias(request, "Distribution list deleted",
                      "Distribution lists deleted")


@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def delforward(request):
    return _del_alias(request, "Forward deleted", "Forwards deleted")
