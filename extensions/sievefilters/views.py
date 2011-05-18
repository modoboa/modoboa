# coding: utf-8

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import _render, ajax_response
from modoboa.auth.lib import get_password
from lib import *
from forms import *

@login_required
def index(request, tplname="sievefilters/index.html"):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    active_script, scripts = sc.listscripts()
    return _render(request, tplname, {
            "active_script" : active_script,
            "scripts" : sorted(scripts)
            })

@login_required
def getscript(request):
    if not request.GET.has_key("name") or request.GET["name"] == "":
        return
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        content = sc.getscript(request.GET["name"])
    except SieveClientError, e:
        pass
    return ajax_response(request, template="sievefilters/rawfilter.html", 
                         name=request.GET["name"], scriptcontent=content)

@login_required
def savescript(request):
    if not request.POST.has_key("scriptname") or \
            not request.POST.has_key("scriptcontent"):
        return
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.pushscript(request.POST["scriptname"],
                      request.POST["scriptcontent"])
    except SieveClientError, e:
        error = str(e)
        return ajax_response(request, "ko", respmsg=error)
        
    return ajax_response(request, respmsg=_("Filters set saved"))
    
@login_required
def new_filters_set(request, tplname="sievefilters/newfiltersset.html"):
    ctx = {"title" : _("Create a new filters set"),
           "fname" : "newfiltersset",
           "submit_label" : _("Create"),
           "withmenu" : False,
           "withunseen" : False}
    if request.method == "POST":
        form = FiltersSetForm(request.POST)
        error = None
        if form.is_valid():
            sc = SieveClient(user=request.user.username, 
                             password=request.session["password"])
            try:
                sc.pushscript(form.cleaned_data["name"], "# Empty script",
                              form.cleaned_data["active"])
            except SieveClientError, e:
                error = str(e)
            else:
                return ajax_response(request, url=reverse(index), 
                                     respmsg=_("Filters set created"))
        ctx["form"] = form
        ctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["form"] = FiltersSetForm()
    return _render(request, tplname, ctx)

@login_required
def delete_filters_set(request):
    if not request.GET.has_key("name") or \
            request.GET["name"] == "":
        return
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.deletescript(request.GET["name"])
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, respmsg=_("Filters set deleted"))

@login_required
def activate_filters_set(request):
    if not request.GET.has_key("name") or \
            request.GET["name"] == "":
        return
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.activatescript(request.GET["name"])
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, respmsg=_("Filters set activated"))
