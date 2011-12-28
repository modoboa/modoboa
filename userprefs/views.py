import copy
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators \
    import login_required, user_passes_test
from django.conf import settings
from django.utils.translation import ugettext as _
from modoboa.lib import parameters, events
from modoboa.lib.webutils import _render, _render_error, ajax_response
from forms import *
from modoboa.admin.models import Mailbox, Alias, AdminError
from modoboa.admin.lib import is_domain_admin
from modoboa.auth.lib import encrypt

@login_required
def index(request):
    return HttpResponseRedirect(reverse(preferences))

@login_required
def changepassword(request, tplname="userprefs/chpassword.html"):
    if request.user.id == 1:
        target = request.user
    else:
        target = Mailbox.objects.get(user=request.user.id)
    res = events.raiseQueryEvent("PasswordChange", user=request.user)
    if True in res:
        ctx = dict(error=_("Password change is disabled for this user"))
        return _render_error(request, errortpl="error_simple", user_context=ctx)

    error = None
    if request.method == "POST":
        form = ChangePasswordForm(target, request.POST)
        if form.is_valid():
            if request.user.id != 1:
                try:
                    target.set_password(form.cleaned_data["oldpassword"],
                                        form.cleaned_data["confirmation"])
                except AdminError, e:
                    error = str(e)
                request.session["password"] = encrypt(request.POST["confirmation"])
            else:
                target.set_password(request.POST["confirmation"])

            if error is None:
                return ajax_response(request, respmsg=_("Password changed"))
        return ajax_response(request, status="ko", template=tplname, 
                             form=form, error=error)

    form = ChangePasswordForm(target)
    return _render(request, 'userprefs/chpassword.html', {
            "form" : form
            })

@login_required
@user_passes_test(lambda u: not u.is_superuser and not is_domain_admin(u))
def setforward(request, tplname="userprefs/setforward.html"):
    mb = Mailbox.objects.get(user=request.user.id)
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
        return ajax_response(request, status="ko", template=tplname,
                             form=form, error=error)
    form = ForwardForm()
    if al is not None:
        form.fields["dest"].initial = al.extmboxes
        try:
            selfmb = al.mboxes.get(pk=mb.id)
        except Mailbox.DoesNotExist:
            pass
        else:
            form.fields["keepcopies"].initial = True
    return _render(request, tplname, {
            "form" : form
            })

@login_required
def preferences(request):
    apps = sorted(parameters._params.keys())
    gparams = []
    for app in apps:
        if not len(parameters._params[app]['U']):
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
            "gparams" : gparams
            })

@login_required
def savepreferences(request):
    for pname, v in request.POST.iteritems():
        if pname == "update":
            continue
        app, name = pname.split('.')
        parameters.save_user(request.user, name, v, app=app)

    return ajax_response(request)

