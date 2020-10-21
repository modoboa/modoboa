"""Simple user views."""

import io

import qrcode
import qrcode.image.svg

from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from django.contrib.auth.decorators import login_required, user_passes_test

import django_otp
from rest_framework.authtoken.models import Token

from modoboa.lib.cryptutils import encrypt
from modoboa.lib.web_utils import render_to_json_response
from modoboa.parameters import tools as param_tools
from .. import signals
from ..forms import APIAccessForm, ProfileForm


@login_required
def index(request, tplname="core/user_index.html"):
    """Render user index page."""
    return render(request, tplname, {"selection": "user"})


@login_required
def profile(request, tplname="core/user_profile.html"):
    """Profile detail/update view."""
    update_password = True
    results = signals.allow_password_change.send(
        sender="profile", user=request.user)
    if True in [result[1] for result in results]:
        update_password = False
    password_url = request.localconfig.parameters.get_value(
        "update_password_url")
    show_password_url = False
    if not request.user.is_local and password_url:
        show_password_url = True
        update_password = False

    if request.method == "POST":
        form = ProfileForm(
            update_password, request.POST, instance=request.user
        )
        if form.is_valid():
            form.save()
            if update_password and form.cleaned_data["confirmation"] != "":
                request.session["password"] = force_text(encrypt(
                    form.cleaned_data["confirmation"]
                ))
            translation.activate(request.user.language)
            request.session[translation.LANGUAGE_SESSION_KEY] = (
                request.user.language)
            return render_to_json_response(_("Profile updated"))
        return render_to_json_response(
            {"form_errors": form.errors}, status=400)

    form = ProfileForm(update_password, instance=request.user)
    return render_to_json_response({
        "content": render_to_string(tplname, {
            "form": form,
            "show_password_url": show_password_url,
            "password_url": password_url
        }, request)
    })


@login_required
def preferences(request):
    if request.method == "POST":
        forms = param_tools.registry.get_forms(
            "user", request.POST, user=request.user)
        for formdef in forms:
            form = formdef["form"]
            if form.is_valid():
                form.save()
                continue
            return render_to_json_response({
                "prefix": form.app, "form_errors": form.errors
            }, status=400)
        request.user.save()
        return render_to_json_response(_("Preferences saved"))

    return render_to_json_response({
        "content": render_to_string("core/user_preferences.html", {
            "forms": param_tools.registry.get_forms(
                "user", user=request.user, first_app="general")
        }, request),
        "onload_cb": "preferencesCallback",
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
        "content": render_to_string(
            "core/api_access.html", {"form": form}, request)
    })


@login_required
def security(request):
    """View to manage security settings."""
    context = {"user_has_device": django_otp.user_has_device(request.user)}
    if not request.user.tfa_enabled:
        device = request.user.staticdevice_set.first()
        if device:
            tokens = device.token_set.all().values_list("token", flat=True)
            context.update({"tokens": tokens})
            # Set enable flag to True so we can't go here anymore
            request.user.tfa_enabled = True
            request.user.save()
        else:
            device = request.user.totpdevice_set.first()
            if device:
                factory = qrcode.image.svg.SvgPathImage
                img = qrcode.make(device.config_url, image_factory=factory)
                buf = io.BytesIO()
                img.save(buf)
                context.update({"qrcode": buf.getvalue().decode()})
    resp = {
        "content": render_to_string(
            "core/user_security.html", context, request),
        "callback": "security"
    }
    return render_to_json_response(resp)
