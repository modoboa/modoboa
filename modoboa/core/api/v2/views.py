"""Core API v2 views."""

import logging

from django.utils.html import escape
from django.utils.translation import ugettext as _

from django.contrib.auth import login

from rest_framework import response, status
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.views import APIView

from modoboa.core.password_hashers import get_password_hasher
from modoboa.parameters import tools as param_tools

from .serializers import *

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


class EmailPasswordResetView(APIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address.
    """

    def post(self, request, *args, **kwargs):
        serializer = EmailPasswordRecoveryInitSerializer(
            data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except UserNotFound:
            return response.Response({"no valid user found"}, 404)
        try:
            serializer.save()
        except EmailSendingFailure:
            return response.Response({"Email failed to send, possibly a misconfiguration?"}, 502)
        # Email response
        return response.Response(status=204)


class DefaultPasswordResetView(EmailPasswordResetView):
    """ 
    Works with PasswordRecoveryForm.vue.
    First checks if SMS recovery is available, else switch to super (Email recovery [with seconday email]).
    """

    def post(self, request, *args, **kwargs):
        """Recover password."""
        serializer = SMSPasswordRecoveryInitSerializer(
            data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except NoSMSAvailable:
            return super().post(request, *args, **kwargs)
        # SMS response
        return response.Response(status=233)


class PasswordResetConfirmSmsCodeView(APIView):
    """ Check SMS Totp code. """

    def post(self, request, *args, **kwargs):
        serializer = PasswordRecoverySmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        payload = serializer.context["response"]
        payload = {"token": payload[0], "id": payload[1]}
        
        return response.Response(payload, 200)
      

class PasswordResetConfirmView(APIView):
    """ Get and set new user password. """

    def post(self, request, *args, **kwargs):
        serializer = PasswordRecoveryConfirmSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (PasswordRequirementsFailure, UserNotFound, InvalidToken) as e:
            if type(e) == PasswordRequirementsFailure:
                errors = []
                for element in e.message_list:
                    errors.append(element)
                return response.Response(errors, 455)
            elif type(e) == UserNotFound:
                return response.Response(status=404)
            elif type(e) == InvalidToken:
                return response.Response(status=401)
        serializer.save()
        return response.Response(status=200)


class PasswordResetResendSmsCodeView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = PasswordRecoverySmsResendSerializer(
            data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(status=200)
