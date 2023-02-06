from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle
from django.urls import resolve

class UserDdosPerView(SimpleRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for authentificated users."""

    scope = 'ddos'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': hash(resolve(request.path).url_name),
            'ident': ident
        }

class UserLesserDdosUser(SimpleRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for authentificated users."""

    scope = 'ddos_lesser'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': hash(resolve(request.path).url_name),
            'ident': ident
        }

class LoginThrottle(SimpleRateThrottle):

    scope = 'login'

    def get_cache_key(self, request, view = None):
            return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

    def reset_cache(self, request):
        self.key = self.get_cache_key(request)
        self.cache.delete(self.key)


class PasswordResetRequestThrottle(LoginThrottle):

    scope = 'password_recovery_request'


class PasswordResetTotpThrottle(LoginThrottle):

    scope = 'password_recovery_totp_check'


class PasswordResetApplyThrottle(LoginThrottle):

    scope = 'password_recovery_apply'

