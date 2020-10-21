"""Core middlewares."""

from django import http
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from . import models


class LocalConfigMiddleware(MiddlewareMixin):
    """A middleware to inject LocalConfig into request."""

    def process_request(self, request):
        """Inject LocalConfig instance to request."""
        request.localconfig = models.LocalConfig.objects.first()


class TwoFAMiddleware:
    """Custom 2FA middleware to enforce verification is used has TFA enabled."""

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        redirect_url = reverse("core:2fa_verify")
        url_exceptions = (
            redirect_url,
            "/jsi18n/"
        )
        condition = (
            user and
            not user.is_anonymous and
            user.tfa_enabled and
            request.path not in url_exceptions and
            not user.is_verified()
        )
        if condition:
            return http.HttpResponseRedirect(reverse("core:2fa_verify"))
        return self.get_response(request)
