# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events
from modoboa.admin import views as admviews
from forms import LoginForm
from modoboa.auth.lib import *

def dologin(request):
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        user = authenticate(username=request.POST["username"], 
                            password=request.POST["password"])
        if user:
            if user.is_active:
                login(request, user)
            
                if request.user.id != 1:
                    request.session["password"] = encrypt(request.POST["password"])

                request.session["django_language"] = \
                    parameters.get_user(request.user, "LANG", app="general")

                events.raiseEvent("UserLogin", request=request, 
                                  username=request.POST["username"],
                                  password=request.POST["password"])

                next = request.POST["next"]
                if next.strip() in ["", "None"]:
                    next = reverse(admviews.domains)
                return HttpResponseRedirect(next)
            else:
                error = _("Account is disabled.")
        error = _("Your username and password didn't match. Please try again.")
    else:
        form = LoginForm()

    next = request.GET.has_key("next") and request.GET["next"] or None
    return render_to_response("registration/login.html", {
            "form" : form, "error" : error, "next" : next, 
            "annoucements" : events.raiseQueryEvent("GetAnnouncement", target="loginpage")
            }, context_instance=RequestContext(request))

def dologout(request):
    events.raiseEvent("UserLogout", request=request)
    logout(request)

    return HttpResponseRedirect(reverse(dologin))
