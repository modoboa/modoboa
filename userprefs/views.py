# coding: utf-8
import copy
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators \
    import login_required, user_passes_test
from django.conf import settings
from django.utils.translation import ugettext as _
from modoboa.lib import parameters, events
from modoboa.lib.webutils import _render, _render_error, ajax_response, \
    ajax_simple_response
from forms import *
from modoboa.admin.models import Mailbox, Alias
from modoboa.admin.lib import AdminError
from modoboa.auth.lib import encrypt

@login_required
def index(request):
    return HttpResponseRedirect(reverse(preferences))

@login_required
def changepassword(request, tplname="common/generic_modal_form.html"):
    res = events.raiseQueryEvent("PasswordChange", request.user)
    if True in res:
        from modoboa.lib.exceptions import ModoboaException
        raise ModoboaException(_("Password change is disabled for this user"))
        # ctx = dict(error=_("Password change is disabled for this user"))
        # return _render_error(request, user_context=ctx)

    ctx = dict(
        title=_("Change password"),
        formid="chpasswordform",
        action=reverse(changepassword),
        action_label=_("Update"),
        action_classes="submit",
        )

    error = None
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            try:
                request.user.set_password(form.cleaned_data["confirmation"],
                                          form.cleaned_data["oldpassword"])
            except AdminError, e:
                error = str(e)
            else:
                request.session["password"] = encrypt(request.POST["confirmation"])
                request.user.save()
            if error is None:
                return ajax_response(request, respmsg=_("Password changed"))
        ctx.update(form=form, error=error)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx.update(form=ChangePasswordForm(request.user))
    return _render(request, tplname, ctx)

@login_required
@user_passes_test(lambda u: u.belongs_to_group('SimpleUsers'))
def setforward(request, tplname="common/generic_modal_form.html"):
    mb = request.user.mailbox_set.all()[0]
    ctx = dict(
        title=_("Define a forward"),
        formid="forwardform",
        action=reverse(setforward),
        action_label=_("Update"),
        action_classes="submit",
        )
    try:
        al = Alias.objects.get(address=mb.address, 
                               domain__name=mb.domain.name)
    except Alias.DoesNotExist:
        al = None
    if request.method == "POST":
        form = ForwardForm(request.POST)
        error = None
        if form.is_valid():
            try:
                if al is None:
                    al = Alias()
                    al.address = mb.address
                    al.domain = mb.domain
                    al.enabled = mb.user.is_active
                intdests = []
                if form.cleaned_data["keepcopies"]:
                    intdests += [mb]
                form.parse_dest()
                al.save(intdests, form.dests)
                return ajax_response(request, respmsg=_("Forward updated"))
            except BadDestination, e:
                error = str(e)
        ctx.update(form=form, error=error)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = ForwardForm()
    if al is not None:
        form.fields["dest"].initial = al.extmboxes
        try:
            selfmb = al.mboxes.get(pk=mb.id)
        except Mailbox.DoesNotExist:
            pass
        else:
            form.fields["keepcopies"].initial = True
    ctx.update(form=form)
    return _render(request, tplname, ctx)

@login_required
def preferences(request):
    apps = sorted(parameters._params.keys())
    gparams = []
    for app in apps:
        if not len(parameters._params[app]['U']):
            continue
        if parameters.get_app_option('U', 'needs_mailbox', False, app=app) \
                and not request.user.has_mailbox:
            continue
            
        tmp = {"name" : app, "params" : []}
        for p in parameters._params_order[app]['U']:
            param_def = parameters._params[app]['U'][p]
            newdef = copy.deepcopy(param_def)
            newdef["name"] = p
            newdef["value"] = parameters.get_user(request.user, p, app=app)
            tmp["params"] += [newdef]
        gparams += [tmp]

    return _render(request, 'userprefs/preferences.html', {
            "selection" : "user",
            "left_selection" : "preferences",
            "gparams" : gparams
            })

@login_required
def savepreferences(request):
    for pname, v in request.POST.iteritems():
        if pname == "update":
            continue
        app, name = pname.split('.')
        parameters.save_user(request.user, name, v, app=app)

    return ajax_simple_response(dict(
            status="ok", message=_("Preferences saved")
            ))
