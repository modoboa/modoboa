from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class UserDosThrottle(UserRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for authentificated users."""

    scope = "ddos"

    def get_cache_key(self, request, view):
        return "throttle_{viewid}_{indent}".format(
            viewid=id(view),
            indent=self.get_indent(request)
        )

class AnonDosThrottle(AnonRateThrottle):
    """Custom Throttle class for rest_framework. The throttling is applied on a per view basis for visitors."""

    scope = "anon_ddos"

    def get_cache_key(self, request, view):
        return "throttle_{viewid}_{indent}".format(
            viewid=id(view),
            indent=self.get_indent(request)
        )
