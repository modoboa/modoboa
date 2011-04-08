import copy
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators \
    import login_required
from django.utils.translation import ugettext as _
from modoboa.lib import _render, ajax_response, parameters
from modoboa.lib import crypt_password
from forms import ChangePasswordForm
from modoboa.admin.models import Mailbox

@login_required
def index(request):
    return HttpResponseRedirect(reverse(preferences))

@login_required
def changepassword(request, tplname="userprefs/chpassword.html"):
    if request.user.id == 1:
        target = request.user
    else:
        target = Mailbox.objects.get(user=request.user.id)
    error = None
    if request.method == "POST":
        form = ChangePasswordForm(target, request.POST)
        if form.is_valid():
            if request.user.id != 1:                
                target.password = crypt_password(request.POST["confirmation"])
            else:
                target.set_password(request.POST["confirmation"])
            target.save()
            return ajax_response(request)
        return ajax_response(request, status="ko", template=tplname, form=form, error=error)

    form = ChangePasswordForm(target)
    return _render(request, 'userprefs/chpassword.html', {
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

