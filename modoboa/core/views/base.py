# -*- coding: utf-8 -*-

"""Base core views."""

from __future__ import unicode_literals

from django.contrib.auth import mixins as auth_mixins
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views import generic

from ..extensions import exts_pool


def find_nextlocation(request, user):
    """Find next location for given user after login."""
    if not user.last_login:
        # Redirect to profile on first login
        return reverse("core:user_index")
    nextlocation = request.POST.get("next", request.GET.get("next"))
    condition = (
        nextlocation and
        is_safe_url(nextlocation, host=request.get_host())
    )
    if condition:
        return nextlocation
    if request.user.role == "SimpleUsers":
        topredir = request.localconfig.parameters.get_value(
            "default_top_redirection")
        if topredir != "user":
            infos = exts_pool.get_extension_infos(topredir)
            nextlocation = infos["topredirection_url"]
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
