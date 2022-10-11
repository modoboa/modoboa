"""Core API v2 views."""

import logging
import oath

from django.utils.html import escape
from django.utils.translation import ugettext as _

from django.contrib.auth import login, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.forms import SetPasswordForm
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from rest_framework import response, status
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.views import APIView 
from modoboa.core.password_hashers import get_password_hasher
from modoboa.parameters import tools as param_tools
from modoboa.lib import cryptutils
from modoboa.core.views.auth import RestPasswordResetView


logger = logging.getLogger("modoboa.auth")

from ... import sms_backends

class TokenObtainPairView(jwt_views.TokenObtainPairView):
    """We overwrite this view to deal with password scheme update."""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(
                _("Failed connection attempt from '%s' as user '%s'"),
                request.META["REMOTE_ADDR"],
                escape(serializer.data["username"])
            )
            raise InvalidToken(e.args[0])

        user = serializer.user
        login(request, user)
        logger.info(
            _("User '%s' successfully logged in"), user.username
        )
        if user and user.is_active:
            condition = (
                user.is_local and
                param_tools.get_global_parameter(
                    "update_scheme", raise_exception=False)
            )
            if condition:
                # check if password scheme is correct
                scheme = param_tools.get_global_parameter(
                    "password_scheme", raise_exception=False)
                # use SHA512CRYPT as default fallback
                if scheme is None:
                    pwhash = get_password_hasher("sha512crypt")()
                else:
                    pwhash = get_password_hasher(scheme)()
                if not user.password.startswith(pwhash.scheme):
                    logger.info(
                        _("Password scheme mismatch. Updating %s password"),
                        user.username
                    )
                    user.set_password(request.data["password"])
                    user.save()
                if pwhash.needs_rehash(user.password):
                    logger.info(
                        _("Password hash parameter missmatch. "
                          "Updating %s password"),
                        user.username
                    )
                    user.set_password(serializer.data["password"])
                    user.save()

        return response.Response(
            serializer.validated_data, status=status.HTTP_200_OK)


class PasswordResetView(RestPasswordResetView):
    
    def post(self, request, *args, **kwargs):
        """Recover password."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.localconfig.parameters.get_value("sms_password_recovery"):
            rep = super().post(request, *args, **kwargs)
            if rep.status_code == 400:
                return response.Response({"status": "wrong_email"}, status=400)
            else:
                return rep
        user = get_user_model()._default_manager.filter(
            email=serializer.validated_data["email"], phone_number__isnull=False
        ).first()
        if not user:
            rep = super().post(request, *args, **kwargs)
            if rep.status_code == 400:
                return response.Response({"status": "wrong_email"}, status=400)
            else:
                return rep
        backend = sms_backends.get_active_backend(
            request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}"
            .format(code)
        )
        if not backend.send(text, [str(user.phone_number)]):
            rep = super().post(request, *args, **kwargs)
            if rep.status_code == 400:
                return response.Response({"status": "wrong_email"}, status=400)
            else:
                return rep
        self.request.session["user_pk"] = user.pk
        self.request.session["totp_secret"] = secret
        return response.Response({"status": "sms"})

INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'

class PasswordResetConfirmView(APIView):
    reset_url_token = 'set-password'
    token_generator = PasswordResetTokenGenerator()

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model()._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None
        return user

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        assert 'uidb64' in kwargs and "token" in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    return HttpResponseRedirect(f"/new_admin/password_recovery/confirm/{kwargs['uidb64']}/set-password")
        return HttpResponseRedirect(f"/new_admin/password_reset_done?fail=true")

    def post(self, request, *args, **kwargs):
        assert "new_password1" in kwargs and "new_password2" in kwargs

        # Only proceed if the INTERNAL RESET SESSION TOKEN is set
        if self.validlink:
            form = SetPasswordForm(self.user)
            form.data = {"new_password1": kwargs["new_password1"], "new_password2": kwargs["new_password2"]}

            if not form.is_valid():
                return HttpResponseRedirect(f"/new_admin/password_reset_done?fail=true")

            form.save()
            return HttpResponseRedirect(f"/new_admin/password_reset_done?fail=false")

        return HttpResponseRedirect(f"/new_admin/password_reset_done?fail=true")




    def post(self, request, *args, **kwargs):
        pass