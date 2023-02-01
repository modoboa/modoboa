from rest_framework.throttling import SimpleRateThrottle

class UserDdosPerView(SimpleRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for authentificated users."""

    scope = 'ddos'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': hash(f"{view.basename}_{view.name}"),
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
            'scope': self.scope,
            'ident': ident
        }
