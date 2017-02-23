# coding: utf-8
"""Core authentication views."""

import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from django.contrib.auth import authenticate, login, logout

from modoboa.core.forms import LoginForm

from .base import find_nextlocation
from .. import signals

logger = logging.getLogger("modoboa.auth")


def dologin(request):
    """Try to authenticate."""
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            logger = logging.getLogger('modoboa.auth')
            user = authenticate(username=form.cleaned_data["username"],
                                password=form.cleaned_data["password"])
            if user and user.is_active:
                login(request, user)
                if not form.cleaned_data["rememberme"]:
                    request.session.set_expiry(0)

                translation.activate(request.user.language)
                request.session[translation.LANGUAGE_SESSION_KEY] = (
                    request.user.language)

                logger.info(
                    _("User '%s' successfully logged in") % user.username
                )
                signals.user_login.send(
                    sender="dologin",
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"])
                return HttpResponseRedirect(find_nextlocation(request, user))
            error = _(
                "Your username and password didn't match. Please try again.")
            logger.warning(
                "Failed connection attempt from '%(addr)s' as user '%(user)s'"
                % {"addr": request.META["REMOTE_ADDR"],
                   "user": form.cleaned_data["username"]}
            )

        nextlocation = request.POST.get("next", None)
        httpcode = 401
    else:
        form = LoginForm()
        nextlocation = request.GET.get("next", None)
        httpcode = 200

    announcements = signals.get_announcements.send(
        sender="login", location="loginpage")
    announcements = [announcement[1] for announcement in announcements]
    return HttpResponse(
        render_to_string(
            "registration/login.html", {
                "form": form, "error": error, "next": nextlocation,
                "annoucements": announcements},
            request),
        status=httpcode)

dologin = never_cache(dologin)


def dologout(request):
    """Logout current user."""
    if not request.user.is_anonymous:
        signals.user_logout.send(sender="dologout", request=request)
        logger = logging.getLogger("modoboa.auth")
        logger.info(_("User {} logged out").format(request.user.username))
        logout(request)
    return HttpResponseRedirect(reverse("core:login"))
