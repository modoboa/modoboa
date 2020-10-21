"""Core authentication views."""

import logging

import oath

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.cache import never_cache

from django.contrib.auth import (
    authenticate, login, logout, views as auth_views
)
from django.contrib.auth.tokens import default_token_generator

from braces.views import (
    JSONResponseMixin, LoginRequiredMixin, UserFormKwargsMixin)
import django_otp

from modoboa.core import forms
from modoboa.core.password_hashers import get_password_hasher
from modoboa.lib import cryptutils
from modoboa.parameters import tools as param_tools

from .. import models
from .. import sms_backends
from .. import signals
from .base import find_nextlocation

logger = logging.getLogger("modoboa.auth")


def dologin(request):
    """Try to authenticate."""
    error = None
    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            logger = logging.getLogger("modoboa.auth")
            user = authenticate(username=form.cleaned_data["username"],
                                password=form.cleaned_data["password"])
            if user and user.is_active:
                if param_tools.get_global_parameter("update_scheme",
                                                    raise_exception=False):
                    # check if password scheme is correct
                    scheme = param_tools.get_global_parameter(
                        "password_scheme", raise_exception=False)
                    # use SHA512CRYPT as default fallback
                    if scheme is None:
                        pwhash = get_password_hasher('sha512crypt')()
                    else:
                        pwhash = get_password_hasher(scheme)()
                    if not user.password.startswith(pwhash.scheme):
                        logging.info(
                            _("Password scheme mismatch. Updating %s password"),
                            user.username
                        )
                        user.set_password(form.cleaned_data["password"])
                        user.save()
                    if pwhash.needs_rehash(user.password):
                        logging.info(
                            _("Password hash parameter missmatch. "
                              "Updating %s password"),
                            user.username
                        )
                        user.set_password(form.cleaned_data["password"])
                        user.save()

                login(request, user)
                if not form.cleaned_data["rememberme"]:
                    request.session.set_expiry(0)

                translation.activate(request.user.language)
                request.session[translation.LANGUAGE_SESSION_KEY] = (
                    request.user.language)

                logger.info(
                    _("User '%s' successfully logged in") % user.username
                )
                signals.user_login.send(
                    sender="dologin",
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"])
                return HttpResponseRedirect(find_nextlocation(request, user))
            error = _(
                "Your username and password didn't match. Please try again.")
            logger.warning(
                "Failed connection attempt from '%(addr)s' as user '%(user)s'"
                % {"addr": request.META["REMOTE_ADDR"],
                   "user": form.cleaned_data["username"]}
            )

        nextlocation = request.POST.get("next", "")
        httpcode = 401
    else:
        form = forms.LoginForm()
        nextlocation = request.GET.get("next", "")
        httpcode = 200

    announcements = signals.get_announcements.send(
        sender="login", location="loginpage")
    announcements = [announcement[1] for announcement in announcements]
    return HttpResponse(
        render_to_string(
            "registration/login.html", {
                "form": form, "error": error, "next": nextlocation,
                "annoucements": announcements},
            request),
        status=httpcode)


dologin = never_cache(dologin)


def dologout(request):
    """Logout current user."""
    if not request.user.is_anonymous:
        signals.user_logout.send(sender="dologout", request=request)
        logger = logging.getLogger("modoboa.auth")
        logger.info(
            _("User '{}' successfully logged out").format(
                request.user.username))
        logout(request)
    return HttpResponseRedirect(reverse("core:login"))


class PasswordResetView(auth_views.PasswordResetView):
    """Custom view to override form."""

    form_class = forms.PasswordResetForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.from_email = request.localconfig.parameters.get_value(
            "sender_address"
        )

    def get_context_data(self, **kwargs):
        """Include help text."""
        context = super().get_context_data(**kwargs)
        context["announcement"] = (
            self.request.localconfig.parameters
            .get_value("password_recovery_msg")
        )
        return context

    def form_valid(self, form):
        """Redirect to code verification page if needed."""
        sms_password_recovery = (
            self.request.localconfig.parameters
            .get_value("sms_password_recovery")
        )
        if not sms_password_recovery:
            return super().form_valid(form)
        user = models.User._default_manager.filter(
            email=form.cleaned_data["email"], phone_number__isnull=False
        ).first()
        if not user:
            # Fallback to email
            return super().form_valid(form)
        backend = sms_backends.get_active_backend(
            self.request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}"
            .format(code)
        )
        if not backend.send(text, [str(user.phone_number)]):
            return super().form_valid(form)
        self.request.session["user_pk"] = user.pk
        self.request.session["totp_secret"] = secret
        return HttpResponseRedirect(reverse("password_reset_confirm_code"))


class VerifySMSCodeView(generic.FormView):
    """View to verify a code received by SMS."""

    form_class = forms.VerifySMSCodeForm
    template_name = "registration/password_reset_confirm_code.html"

    def get_form_kwargs(self):
        """Include totp secret in kwargs."""
        kwargs = super().get_form_kwargs()
        try:
            kwargs.update({"totp_secret": self.request.session["totp_secret"]})
        except KeyError:
            raise Http404
        return kwargs

    def form_valid(self, form):
        """Redirect to reset password form."""
        user = models.User.objects.get(pk=self.request.session.pop("user_pk"))
        self.request.session.pop("totp_secret")
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse("password_reset_confirm", args=[uid, token])
        return HttpResponseRedirect(url)


class ResendSMSCodeView(JSONResponseMixin, generic.View):
    """A view to resend validation code."""

    def get(self, request, *args, **kwargs):
        sms_password_recovery = (
            self.request.localconfig.parameters
            .get_value("sms_password_recovery")
        )
        if not sms_password_recovery:
            raise Http404
        try:
            user = models.User._default_manager.get(
                pk=self.request.session["user_pk"])
        except KeyError:
            raise Http404
        backend = sms_backends.get_active_backend(
            self.request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}"
            .format(code)
        )
        if not backend.send(text, [user.phone_number]):
            raise Http404
        self.request.session["totp_secret"] = secret
        return self.render_json_response({"status": "ok"})


class TwoFactorCodeVerifyView(LoginRequiredMixin,
                              UserFormKwargsMixin,
                              generic.FormView):
    """View to verify a 2FA code after login."""

    form_class = forms.Verify2FACodeForm
    template_name = "registration/twofactor_code_verify.html"

    def form_valid(self, form):
        """Login user."""
        django_otp.login(self.request, form.cleaned_data["tfa_code"])
        return HttpResponseRedirect(
            find_nextlocation(self.request, self.request.user)
        )
