"""Core authentication views."""

from functools import cached_property
import logging
import urllib.parse

import oath

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _
from django.views import generic
from django.views.decorators.http import require_http_methods

from django.contrib.auth import load_backend, login, logout
from django.contrib.auth.tokens import default_token_generator
import django.contrib.auth.views as auth_views

import django_otp
from rest_framework.views import APIView

from modoboa.core import constants, fido2_auth, forms, models
from modoboa.core.api.v2 import serializers
from modoboa.core.password_hashers import get_password_hasher
from modoboa.lib import cryptutils
from modoboa.parameters import tools as param_tools

from .. import sms_backends
from .. import signals
from .base import find_nextlocation

logger = logging.getLogger("modoboa.auth")


class LoginViewMixin:
    @cached_property
    def logger(self):
        return logging.getLogger("modoboa.auth")

    def get_user(self):
        try:
            user_id = self.request.session[constants.TFA_PRE_VERIFY_USER_PK]
            backend_path = self.request.session[constants.TFA_PRE_VERIFY_USER_BACKEND]
            assert backend_path in settings.AUTHENTICATION_BACKENDS
            backend = load_backend(backend_path)
            user = backend.get_user(user_id)
            if user is not None:
                user.backend = backend_path
            return user
        except (KeyError, AssertionError):
            return None

    def login(self, user, rememberme):
        encrypted_password = self.request.session.pop("password", None)
        login(self.request, user)
        # FIXME: remove ASAP
        if encrypted_password:
            self.request.session["password"] = encrypted_password
        if not rememberme:
            self.request.session.set_expiry(0)

        translation.activate(user.language)

        self.logger.info(_("User '%s' successfully logged in") % user.username)
        response = HttpResponseRedirect(find_nextlocation(self.request, user))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user.language)
        return response


class LoginView(LoginViewMixin, auth_views.LoginView):
    """Login view with 2FA support."""

    form_class = forms.AuthenticationForm
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcements = signals.get_announcements.send(
            sender="login", location="loginpage"
        )
        announcements = [announcement[1] for announcement in announcements]
        context.update({"announcements": announcements})
        return context

    def check_password_hash(self, user, form):
        condition = user.is_local and param_tools.get_global_parameter(
            "update_scheme", raise_exception=False
        )
        if not condition:
            return
        # check if password scheme is correct
        scheme = param_tools.get_global_parameter(
            "password_scheme", raise_exception=False
        )
        # use SHA512CRYPT as default fallback
        if scheme is None:
            pwhash = get_password_hasher("sha512crypt")()
        else:
            pwhash = get_password_hasher(scheme)()
        if not user.password.startswith(pwhash.scheme):
            logging.info(
                _("Password scheme mismatch. Updating %s password"),
                user.username,
            )
            user.set_password(form.cleaned_data["password"])
            user.save()
        if pwhash.needs_rehash(user.password):
            logging.info(
                _("Password hash parameter missmatch. " "Updating %s password"),
                user.username,
            )
            user.set_password(form.cleaned_data["password"])
            user.save()

    def form_valid(self, form):
        user = form.get_user()
        self.check_password_hash(user, form)
        # FIXME: remove ASAP
        signals.user_login.send(
            sender="LoginView",
            user=user,
            password=form.cleaned_data["password"],
        )
        if user.tfa_enabled:
            self.request.session[constants.TFA_PRE_VERIFY_USER_PK] = user.pk
            self.request.session[constants.TFA_PRE_VERIFY_USER_BACKEND] = user.backend
            self.request.session["rememberme"] = form.cleaned_data["rememberme"]
            nextlocation = self.request.POST.get("next", self.request.GET.get("next"))
            url = reverse("core:2fa_verify")
            if nextlocation:
                url += f"?next={urllib.parse.quote(nextlocation)}"
            return HttpResponseRedirect(url)
        return self.login(user, form.cleaned_data["rememberme"])

    def form_invalid(self, form):
        # FIXME: should we return a 401 as before ?
        self.logger.warning(
            "Failed connection attempt from '{addr}' as user '{user}'".format(
                addr=self.request.META["REMOTE_ADDR"],
                user=escape(form.cleaned_data["username"]),
            )
        )
        return self.render_to_response(self.get_context_data(form=form), status=401)


@require_http_methods(["POST"])
def dologout(request):
    """Logout current user."""
    if not request.user.is_anonymous:
        signals.user_logout.send(sender="dologout", request=request)
        logger = logging.getLogger("modoboa.auth")
        logger.info(
            _("User '{}' successfully logged out").format(request.user.username)
        )
        logout(request)
    return HttpResponseRedirect(reverse("core:login"))


class PasswordResetView(auth_views.PasswordResetView):
    """Custom view to override form."""

    form_class = forms.PasswordResetForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.from_email = request.localconfig.parameters.get_value("sender_address")

    def get_context_data(self, **kwargs):
        """Include help text."""
        context = super().get_context_data(**kwargs)
        context["announcement"] = self.request.localconfig.parameters.get_value(
            "password_recovery_msg"
        )
        return context

    def form_valid(self, form):
        """Redirect to code verification page if needed."""
        sms_password_recovery = self.request.localconfig.parameters.get_value(
            "sms_password_recovery"
        )
        if not sms_password_recovery:
            return super().form_valid(form)
        user = models.User._default_manager.filter(
            email=form.cleaned_data["email"], phone_number__isnull=False
        ).first()
        if not user:
            # Fallback to email
            return super().form_valid(form)
        backend = sms_backends.get_active_backend(self.request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}".format(
                code
            )
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
            raise Http404 from None
        return kwargs

    def form_valid(self, form):
        """Redirect to reset password form."""
        user = models.User.objects.get(pk=self.request.session.pop("user_pk"))
        self.request.session.pop("totp_secret")
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse("password_reset_confirm", args=[uid, token])
        return HttpResponseRedirect(url)


class ResendSMSCodeView(generic.View):
    """A view to resend validation code."""

    def get(self, request, *args, **kwargs):
        sms_password_recovery = self.request.localconfig.parameters.get_value(
            "sms_password_recovery"
        )
        if not sms_password_recovery:
            raise Http404 from None
        try:
            user = models.User._default_manager.get(pk=self.request.session["user_pk"])
        except KeyError:
            raise Http404 from None
        backend = sms_backends.get_active_backend(self.request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}".format(
                code
            )
        )
        if not backend.send(text, [user.phone_number]):
            raise Http404 from None
        self.request.session["totp_secret"] = secret
        return JsonResponse({"status": "ok"})


class TwoFactorCodeVerifyView(LoginViewMixin, generic.FormView):
    """View to verify a 2FA code after login."""

    form_class = forms.Verify2FACodeForm
    template_name = "registration/twofactor_code_verify.html"

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user()
        if not self.user:
            return HttpResponseRedirect(reverse("core:login"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        has_totp_device = django_otp.user_has_device(self.user)
        context["totp_device"] = has_totp_device
        context["webauthn_device"] = self.user.webauthn_enabled
        context["show_method_selection"] = (
            has_totp_device and self.user.webauthn_enabled
        )
        context["nextlocation"] = self.request.POST.get(
            "next", self.request.GET.get("next")
        )
        if context["nextlocation"] is None:
            context.pop("nextlocation")
        return context

    def form_valid(self, form):
        """Login user."""
        response = self.login(self.user, self.request.session.pop("rememberme", False))
        django_otp.login(self.request, form.cleaned_data["tfa_code"])
        return response


class FidoAuthenticationBeginView(generic.View):
    """FIDO authentication process, begining."""

    def post(self, request, *args, **kwargs):
        user_id = request.session.get(constants.TFA_PRE_VERIFY_USER_PK)
        if not user_id:
            raise PermissionDenied
        options, state = fido2_auth.begin_authentication(request, user_id)
        request.session["fido_state"] = state
        return JsonResponse(dict(options))


class FidoAuthenticationEndView(LoginViewMixin, APIView):
    """FIDO authentication process, end."""

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        fido_state = request.session.pop("fido_state", None)
        if not user or not fido_state:
            raise PermissionDenied
        serializer = serializers.FidoAuthenticationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fido2_auth.end_authentication(
            user, fido_state, serializer.validated_data, request.localconfig.site.domain
        )
        response = self.login(user, self.request.session.pop("rememberme", False))
        return JsonResponse({"next": response.url})
