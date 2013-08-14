from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required, user_passes_test
from modoboa.lib import events, parameters
from modoboa.lib.webutils import (
    ajax_simple_response, _render_to_string
)
from modoboa.lib.cryptutils import encrypt
from modoboa.core.forms import ProfileForm


@login_required
def index(request, tplname="core/user_index.html"):
    extrajs = events.raiseQueryEvent("ExtraUprefsJS", request.user)
    return render(request, tplname, {
        "selection": "user",
        "extrajs": "".join(extrajs)
    })


@login_required
def profile(request, tplname='core/user_profile.html'):
    update_password = True
    if True in events.raiseQueryEvent("PasswordChange", request.user):
        update_password = False

    if request.method == "POST":
        form = ProfileForm(
            update_password, request.POST, instance=request.user
        )
        if form.is_valid():
            form.save()
            if update_password and form.cleaned_data["confirmation"] != "":
                request.session["password"] = encrypt(form.cleaned_data["confirmation"])
            return ajax_simple_response(dict(
                status="ok", respmsg=_("Profile updated")
            ))
        return ajax_simple_response({
            "status": "ko",
            "errors": form.errors
        })

    form = ProfileForm(update_password, instance=request.user)
    return ajax_simple_response({
        "status": "ok",
        "content": _render_to_string(request, tplname, {
            "form": form
        })
    })


@login_required
def preferences(request):
    if request.method == "POST":
        for formdef in parameters.get_user_forms(request.user, request.POST)():
            form = formdef["form"]
            if form.is_valid():
                form.save()
                continue
            return ajax_simple_response({
                "status": "ko", "prefix": form.app, "errors": form.errors
            })

        return ajax_simple_response({
            "status": "ok", "respmsg": _("Preferences saved")
        })

    return ajax_simple_response({
        "status": "ok",
        "content": _render_to_string(request, "core/user_preferences.html", {
            "forms": parameters.get_user_forms(request.user)
        })
    })
