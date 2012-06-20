# coding: utf-8
import copy
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators \
    import login_required, user_passes_test
from django.conf import settings
from django.utils.translation import ugettext as _
from modoboa.lib import parameters, events
from modoboa.lib.webutils import ajax_response, ajax_simple_response
from forms import *
from modoboa.admin.models import Mailbox, Alias
from modoboa.admin.lib import AdminError
from modoboa.auth.lib import encrypt

@login_required
def index(request):
    return HttpResponseRedirect(reverse(profile))

@login_required
@user_passes_test(lambda u: u.belongs_to_group('SimpleUsers'))
def forward(request):
    mb = request.user.mailbox_set.all()[0]
    ctx = dict(
        title=_("Forward"), 
        subtitle=_("Automatically forward emails to another address"),
        action=reverse(forward),
        left_selection="forward",
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
        return ajax_simple_response(dict(
                status="ko", 
                content=render_to_string("userprefs/form.html", dict(form=form)),
                respmsg=error
                ))

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
    return render(request, "userprefs/section.html", ctx)

@login_required
def profile(request):
    update_password = True
    if True in events.raiseQueryEvent("PasswordChange", request.user):
        update_password = False

    if request.method == "POST":
        form = ProfileForm(update_password, request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if update_password:
                request.session["password"] = encrypt(form.cleaned_data["confirmation"])
            return ajax_simple_response(dict(
                    status="ok", respmsg=_("Profile updated")
                    ))
        return ajax_simple_response(dict(
                status="ko", 
                content=render_to_string("userprefs/form.html", dict(form=form))
                ))

    form = ProfileForm(update_password, instance=request.user)
    return render(request, 'userprefs/section.html', {
            "title" : _("Profile"), 
            "subtitle" : _("Update your personal information"),
            "action" : reverse(profile),
            "left_selection" : "profile",
            "form" : form
            })

@login_required
def preferences(request):
    if request.method == "POST":
        for pname, v in request.POST.iteritems():
            if pname == "update":
                continue
            app, name = pname.split('.')
            parameters.save_user(request.user, name, v, app=app)

        return ajax_simple_response(dict(
                status="ok", message=_("Preferences saved")
                ))

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

    return render(request, 'userprefs/preferences.html', {
            "selection" : "user",
            "left_selection" : "preferences",
            "gparams" : gparams
            })
