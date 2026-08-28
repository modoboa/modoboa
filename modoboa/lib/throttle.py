from django.shortcuts import render
from django.urls import resolve
from django.utils.translation import gettext as _

from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class UserDdosPerView(SimpleRateThrottle):
    """
    Custom Throttle class for rest_framework. The throttling is
    applied on a per view basis for authentificated users.
    """

    scope = "ddos"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": hash(resolve(request.path).url_name),
            "ident": ident,
        }


class UserLesserDdosUser(UserDdosPerView):
    """
    Custom Throttle class for rest_framework. The throttling is
    applied on a per view basis for authentificated users.
    """

    scope = "ddos_lesser"


class LoginThrottle(SimpleRateThrottle):
    """Custom throttle to reset the cache counter on success."""

    scope = "login"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }

    def reset_cache(self, request):
        self.key = self.get_cache_key(request, None)
        self.cache.delete(self.key)


class PasswordResetRequestThrottle(LoginThrottle):
    scope = "password_recovery_request"


class PasswordResetTotpThrottle(LoginThrottle):
    scope = "password_recovery_totp_check"


class PasswordResetApplyThrottle(LoginThrottle):
    scope = "password_recovery_apply"


class ThrottleViewMixin:
    """Apply DRF throttle classes to a plain Django class based view.

    The throttle classes defined above only need ``request.META`` and the
    cache, so they work as is with a regular ``HttpRequest``. Reusing them
    here means the Django views and their API v2 counterparts share the same
    scopes, rates and counters.
    """

    throttle_classes: list = []
    throttled_methods: tuple = ("POST",)

    def get_throttles(self):
        """Instantiate throttles once per request."""
        if not hasattr(self, "_throttles"):
            self._throttles = [klass() for klass in self.throttle_classes]
        return self._throttles

    def dispatch(self, request, *args, **kwargs):
        if request.method in self.throttled_methods:
            for throttle in self.get_throttles():
                if not throttle.allow_request(request, self):
                    return self.throttled_response(request, throttle)
        return super().dispatch(request, *args, **kwargs)

    def throttled_response(self, request, throttle):
        """Return the response sent once the rate limit is reached."""
        response = render(
            request,
            "common/error.html",
            {"error": _("Too many attempts, please try again later.")},
            status=429,
        )
        wait = throttle.wait()
        if wait:
            response["Retry-After"] = str(int(wait))
        return response

    def reset_throttles(self, request):
        """Clear counters, to call once a request legitimately succeeded."""
        for throttle in self.get_throttles():
            if hasattr(throttle, "reset_cache"):
                throttle.reset_cache(request)


class GetThrottleViewsetMixin:
    """
    Override default get_throttle behaviour to assign throttle
    classes to different actions.
    """

    def get_throttles(self):
        """Give lesser_ddos to GET type actions and ddos to others."""

        throttles = [UserRateThrottle()]
        actions = [
            "list",
            "retrieve",
            "validate",
            "dns_detail",
            "me",
            "dns_detail",
            "applications",
            "structure",
        ]
        if self.action in actions:
            throttles.append(UserLesserDdosUser())
        else:
            throttles.append(UserDdosPerView())
        return throttles
