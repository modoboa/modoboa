"""Simple user views."""

from django.shortcuts import render
from django.utils import translation
from django.utils.translation import ugettext as _

from django.contrib.auth.decorators import login_required, user_passes_test

from rest_framework.authtoken.models import Token

from modoboa.lib import events, parameters
from modoboa.lib.cryptutils import encrypt
from modoboa.lib.web_utils import (
    _render_to_string, render_to_json_response
)
from ..forms import ProfileForm, APIAccessForm


@login_required
def index(request, tplname="core/user_index.html"):
    extrajs = events.raiseQueryEvent("ExtraUprefsJS", request.user)
    return render(request, tplname, {
        "selection": "user",
        "extrajs": "".join(extrajs)
    })


@login_required
def profile(request, tplname='core/user_profile.html'):
    """Profile detail/update view."""
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
                request.session["password"] = encrypt(
                    form.cleaned_data["confirmation"])
            translation.activate(request.user.language)
            request.session[translation.LANGUAGE_SESSION_KEY] = (
                request.user.language)
            return render_to_json_response(_("Profile updated"))
        return render_to_json_response(
            {'form_errors': form.errors}, status=400)

    form = ProfileForm(update_password, instance=request.user)
    return render_to_json_response({
        "content": _render_to_string(request, tplname, {
            "form": form
        })
    })


@login_required
def preferences(request):
    if request.method == "POST":
        for formdef in parameters.get_user_forms(request.user, request.POST):
            form = formdef["form"]
            if form.is_valid():
                form.save()
                continue
            return render_to_json_response({
                "prefix": form.app, "form_errors": form.errors
            }, status=400)

        return render_to_json_response(_("Preferences saved"))

    return render_to_json_response({
        "content": _render_to_string(request, "core/user_preferences.html", {
            "forms": parameters.get_user_forms(request.user)
        })
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def api_access(request):
    """A view to configure API access."""
    if request.method == "POST":
        form = APIAccessForm(request.POST, user=request.user)
        if form.is_valid():
            if form.cleaned_data.get("enable_api_access"):
                Token.objects.get_or_create(user=request.user)
            else:
                Token.objects.filter(user=request.user).delete()
            return render_to_json_response(_("Access updated"))
        return render_to_json_response({
            "form_errors": form.errors
        }, status=400)
    form = APIAccessForm(user=request.user)
    return render_to_json_response({
        "content": _render_to_string(
            request, "core/api_access.html", {"form": form})
    })
