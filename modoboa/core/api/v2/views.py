"""Core API v2 views."""

import logging
import oath

from django.core.exceptions import ValidationError

from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext as _

from django.views.decorators.cache import never_cache

from django.db.models import Q

from django.contrib.auth import login, get_user_model, password_validation
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import response, status
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.views import APIView

from modoboa.core.password_hashers import get_password_hasher
from modoboa.parameters import tools as param_tools
from modoboa.lib import cryptutils
from modoboa.core.forms import PasswordResetForm

from ... import sms_backends
from .serializers import PasswordRecoverySerializer, PasswordRecoveryResetSerializer

logger = logging.getLogger("modoboa.auth")


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


class RestPasswordResetView(APIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address
    """

    throttle_classes = ()
    permission_classes = ()
    serializer_class = PasswordRecoverySerializer
    authentication_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        if (get_user_model()._default_manager.filter(
                email__iexact=email, is_active=True)
               .exclude(Q(secondary_email__isnull=True) | Q(secondary_email=""))).count() == 0:
            return response.Response({"Status": "no_user"}, status=404)

        form = PasswordResetForm(data={"email": email})
        if not form.is_valid():
            pass
        #form.email = email

        form.save(email_template_name="registration/password_reset_email_v2.html")

        # let whoever receives this signal handle sending the email for the password reset
        return response.Response({"Status": "email_sent"}, status=210)


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
        return response.Response({"status": "sms"}, status=233)


class PasswordResetConfirmView(APIView):
    throttle_classes = ()
    permission_classes = ()
    token_generator = PasswordResetTokenGenerator()
    authentication_classes = ()

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model()._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None
        return user

    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        serializer = PasswordRecoveryResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_user(serializer.data["id"])

        if user is None:
            return response.Response(data={"status": "user_not_found"}, status=404)
        token = serializer.data["token"]

        if self.token_generator.check_token(user, token):
            password = serializer.data["new_password1"]
            try:
                password_validation.validate_password(password, user)
            except ValidationError as e:
                status_message = getattr(e, 'message', _(
                    "Password doesn't not comply with standards"))
                return response.Response(data={"status": status_message}, status=520)
            user.set_password(password)
            user.save()
            return response.Response(data={"status": "success"}, status=200)

        return response.Response(data={"status": "token_incorrect"}, status=401)
