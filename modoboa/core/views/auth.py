# coding: utf-8
import logging

from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from modoboa.core.forms import LoginForm
from modoboa.lib import events, parameters
from modoboa.lib.web_utils import _render_to_string

from ..extensions import exts_pool

logger = logging.getLogger("modoboa.auth")


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
                    _("User '%s' successfully logged in" % user.username)
                )
                events.raiseEvent("UserLogin", request,
                                  form.cleaned_data["username"],
                                  form.cleaned_data["password"])
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

    return HttpResponse(_render_to_string(request, "registration/login.html", {
        "form": form, "error": error, "next": nextlocation,
        "annoucements": events.raiseQueryEvent("GetAnnouncement", "loginpage")
    }), status=httpcode)

dologin = never_cache(dologin)


def dologout(request):
    """Logout the current user.
    """
    if not request.user.is_anonymous():
        events.raiseEvent("UserLogout", request)
        logger = logging.getLogger("modoboa.auth")
        logger.info(_("User '%s' logged out" % request.user.username))
        logout(request)
    return HttpResponseRedirect(reverse("core:login"))
