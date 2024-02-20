from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
from django.urls import resolve


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
