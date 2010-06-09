# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from mailng.lib import events
import mailng.admin
from forms import LoginForm

def dologin(request):
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        user = authenticate(username=request.POST["username"], 
                            password=request.POST["password"])
        if user:
            if user.is_active:
                login(request, user)
            
                events.raiseEvent("UserLogin", request=request, 
                                  username=request.POST["username"],
                                  password=request.POST["password"])

                next = request.POST["next"]
                if next == "None":
                    next = reverse(mailng.admin.views.domains)
                return HttpResponseRedirect(next)
            else:
                error = _("Account is disabled.")
        error = _("Your username and password didn't match. Please try again.")
    else:
        form = LoginForm()
    next = request.GET.has_key("next") and request.GET["next"] or None
    return render_to_response("registration/login.html", {
            "form" : form, "error" : error, "next" : next
            })

def dologout(request):
    events.raiseEvent("UserLogout", request=request)
    logout(request)

    return HttpResponseRedirect(reverse(dologin))
