# coding: utf-8
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events
from modoboa.lib.webutils import _render
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
            if user:
                if user.is_active:
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
                else:
                    error = _("Account is disabled.")
            error = _("Your username and password didn't match. Please try again.")
        next = request.POST.get("next", None)
    else:
        form = LoginForm()
        next = request.GET.get("next", None)

    return _render(request, "registration/login.html", {
            "form" : form, "error" : error, "next" : next, 
            "annoucements" : events.raiseQueryEvent("GetAnnouncement", "loginpage")
            })

dologin = never_cache(dologin)

def dologout(request):
    events.raiseEvent("UserLogout", request)
    logout(request)

    return HttpResponseRedirect(reverse(dologin))
