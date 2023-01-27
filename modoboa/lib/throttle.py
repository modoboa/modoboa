from rest_framework.throttling import SimpleRateThrottle

class UserDosThrottle(SimpleRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for authentificated users."""

    scope = "ddos"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': id(view),
            'ident': ident
        }