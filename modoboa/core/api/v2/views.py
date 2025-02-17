"""Core API v2 views."""

from functools import reduce
import logging
from smtplib import SMTPException

from django.utils.datastructures import MultiValueDictKeyError

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, response
from rest_framework.views import APIView

from modoboa.core import signals
from modoboa.core.utils import check_for_updates
from modoboa.lib.permissions import IsSuperUser
from modoboa.lib.throttle import (
    UserLesserDdosUser,
    PasswordResetApplyThrottle,
    PasswordResetRequestThrottle,
    PasswordResetTotpThrottle,
)

from . import serializers

logger = logging.getLogger("modoboa.auth")


def delete_cache_key(class_target, throttles: list, request) -> None:
    """Attempt to delete cache key from throttling on login/password reset success."""

    for throttle in throttles:
        if isinstance(throttle, class_target):
            throttle.reset_cache(request)
            return


class EmailPasswordResetView(APIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address.
    """

    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request, *args, **kwargs):
        serializer = serializers.PasswordRecoveryEmailSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except SMTPException:
            return response.Response(
                {
                    "type": "email",
                    "reason": "Error while sending the email. Please contact an administrator.",
                },
                503,
            )

        # Email response
        return response.Response({"type": "email"}, 200)


class DefaultPasswordResetView(EmailPasswordResetView):
    """
    Works with PasswordRecoveryForm.vue.
    First checks if SMS recovery is available, else switch to super (Email recovery [with secondary email]).
    """

    def post(self, request, *args, **kwargs):
        """Recover password."""
        serializer = serializers.PasswordRecoverySmsSerializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.NoSMSAvailable:
            return super().post(request, *args, **kwargs)

        # SMS response
        return response.Response({"type": "sms"}, 200)


class PasswordResetSmsTOTP(APIView):
    """Check SMS Totp code."""

    throttle_classes = [PasswordResetTotpThrottle]

    def post(self, request, *args, **kwargs):
        try:
            if request.data["type"] == "confirm":
                klass = serializers.PasswordRecoverySmsConfirmSerializer
            elif request.data["type"] == "resend":
                klass = serializers.PasswordRecoverySmsResendSerializer
            serializer = klass(data=request.data, context={"request": request})
        except (MultiValueDictKeyError, KeyError):
            return response.Response({"reason": "No type provided."}, 400)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        payload = {"type": "resend"}
        if request.data["type"] == "confirm":
            serializer_response = serializer.context["response"]
            payload.update(
                {
                    "token": serializer_response[0],
                    "id": serializer_response[1],
                    "type": "confirm",
                }
            )
        delete_cache_key(PasswordResetTotpThrottle, self.get_throttles(), request)
        return response.Response(payload, 200)


class PasswordResetConfirmView(APIView):
    """Get and set new user password."""

    throttle_classes = [PasswordResetApplyThrottle]

    def post(self, request, *args, **kwargs):
        serializer = serializers.PasswordRecoveryConfirmSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.PasswordRequirementsFailure as e:
            data = {"type": "password_requirement"}
            errors = []
            for element in e.message_list:
                errors.append(element)
            data.update({"errors": errors})
            return response.Response(data, 400)
        serializer.save()
        delete_cache_key(PasswordResetApplyThrottle, self.get_throttles(), request)
        return response.Response(status=200)


class ComponentsInformationAPIView(APIView):
    """Retrieve information about installed components."""

    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.ModoboaComponentSerializer(many=True))
    def get(self, request, *args, **kwargs):
        status, extensions = check_for_updates()
        serializer = serializers.ModoboaComponentSerializer(extensions, many=True)
        return response.Response(serializer.data)


class NotificationsAPIView(APIView):
    """Return list of active notifications."""

    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.NotificationSerializer(many=True))
    def get(self, request, *args, **kwargs):
        notifications = signals.get_top_notifications.send(
            sender="top_notifications", include_all=False
        )
        notifications = reduce(
            lambda a, b: a + b, [notif[1] for notif in notifications]
        )
        serializer = serializers.NotificationSerializer(notifications, many=True)
        return response.Response(serializer.data)
