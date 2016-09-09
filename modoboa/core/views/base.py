"""Base core views."""

from django.core.urlresolvers import reverse
from django.views import generic

from django.contrib.auth import mixins as auth_mixins

from modoboa.lib import parameters

from ..extensions import exts_pool


def find_nextlocation(request, user):
    """Find next location for given user after login."""
    if not user.last_login:
        # Redirect to profile on first login
        return reverse("core:user_index")
    nextlocation = request.POST.get("next", None)
    if nextlocation is None or nextlocation == "None":
        if request.user.role == "SimpleUsers":
            topredir = parameters.get_admin("DEFAULT_TOP_REDIRECTION")
            if topredir != "user":
                infos = exts_pool.get_extension_infos(topredir)
                nextlocation = infos["url"] if infos["url"] else infos["name"]
            else:
                nextlocation = reverse("core:user_index")
        else:
            nextlocation = reverse("core:dashboard")
    return nextlocation


class RootDispatchView(auth_mixins.LoginRequiredMixin, generic.RedirectView):
    """Handle root dispatching based on role."""

    def get_redirect_url(self):
        """Find proper next hop."""
        return find_nextlocation(self.request, self.request.user)
