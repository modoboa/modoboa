# coding: utf-8
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events
from modoboa.lib.webutils import _render_to_string
from modoboa.lib.sysutils import log_warning
from modoboa.admin import views as admviews
from forms import LoginForm
from modoboa.auth.lib import *

def dologin(request):
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], 
                                password=form.cleaned_data["password"])
            if user and user.is_active:
                if not form.cleaned_data["rememberme"]:
                    request.session.set_expiry(0)
                login(request, user)            
                if request.user.id != 1:
                    request.session["password"] = encrypt(request.POST["password"])

                request.session["django_language"] = \
                    parameters.get_user(request.user, "LANG", app="general")

                events.raiseEvent("UserLogin", request, 
                                  form.cleaned_data["username"],
                                  form.cleaned_data["password"])

                next = request.POST["next"]
                if next.strip() in ["", "None"]:
                    next = reverse(admviews.domains)
                return HttpResponseRedirect(next)
            error = _("Your username and password didn't match. Please try again.")
            log_warning("Failed connection attempt from %(addr)s as user %(user)s" \
                            % {"addr" : request.META["REMOTE_ADDR"], 
                               "user" : form.cleaned_data["username"]})

        next = request.POST.get("next", None)
        httpcode = 401
    else:
        form = LoginForm()
        next = request.GET.get("next", None)
        httpcode = 200

    return HttpResponse(_render_to_string(request, "registration/login.html", {
                "form" : form, "error" : error, "next" : next, 
                "annoucements" : events.raiseQueryEvent("GetAnnouncement", "loginpage")
                }), status=httpcode)

dologin = never_cache(dologin)

def dologout(request):
    events.raiseEvent("UserLogout", request)
    logout(request)

    return HttpResponseRedirect(reverse(dologin))
