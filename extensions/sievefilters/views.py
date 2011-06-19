# coding: utf-8

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import _render, _render_to_string, \
    ajax_response, ajax_simple_response, parameters
from modoboa.auth.lib import get_password
from lib import *
from forms import *

@login_required
def index(request, tplname="sievefilters/index.html"):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    active_script, scripts = sc.listscripts()
    if active_script is None:
        active_script = ""
    return _render(request, tplname, {
            "active_script" : active_script,
            "scripts" : sorted(scripts),
            })

@login_required
def get_templates(request, ftype):
    if ftype == "condition":
        return ajax_simple_response(FilterForm.cond_templates)
    return ajax_simple_response(FilterForm.action_templates)

@login_required
def get_user_folders(request):
    from modoboa.extensions.webmail.lib import IMAPconnector

    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    ret = mbc.getfolders(request.user, unseen_messages=False)
    return ajax_simple_response(ret)

@login_required
def getfs(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    editormode = parameters.get_user(request.user, "EDITOR_MODE")
    try:
        content = sc.getscript(name, format=editormode)
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))

    if editormode == "raw":
        return ajax_response(request, template="sievefilters/rawfilter.html", 
                             name=name, scriptcontent=content)
    return ajax_response(request, template="sievefilters/guieditor.html",
                         fs=content)

def build_filter_ctx(ctx, form):
    ctx["form"] = form
    ctx["conds_nb"] = range(form.conds_cnt)
    ctx["actions_nb"] = range(form.actions_cnt)
    return ctx

def submitfilter(request, setname, okmsg, tplname, tplctx, update=False, sc=None):
    form = build_filter_form_from_qdict(request)
    if form.is_valid():
        if sc is None:
            sc = SieveClient(user=request.user.username, 
                             password=request.session["password"])
        fset = sc.getscript(setname, format="fset")
        conditions, actions = form.tofilter()
        if not update:
            fset.addfilter(form.cleaned_data["name"], conditions, actions,
                           form.cleaned_data["match_type"])
        else:
            fset.updatefilter(request.POST["oldname"],
                              form.cleaned_data["name"], conditions, actions,
                              form.cleaned_data["match_type"])
        sc.pushscript(fset.name, str(fset))
        return ajax_response(request, respmsg=okmsg, ajaxnav=True)
    tplctx = build_filter_ctx(tplctx, form)
    return ajax_response(request, status="ko", template=tplname, **tplctx)

@login_required
def newfilter(request, setname, tplname="sievefilters/filter.html"):
    ctx = {"title" : _("New filter"),
           "actionurl" : reverse(newfilter, args=[setname])}
    if request.method == "POST":
        return submitfilter(request, setname, _("Filter created"), tplname, ctx)

    conds = [("Subject", "contains", "")]
    actions = [("fileinto", "")]
    form = FilterForm(conds, actions, request)
    ctx = build_filter_ctx(ctx, form)
    return _render(request, tplname, ctx)

@login_required
def editfilter(request, setname, fname, tplname="sievefilters/filter.html"):
    ctx = {"title" : _("Edit filter"),
           "actionurl" : reverse(editfilter, args=[setname, fname])}
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    if request.method == "POST":
        return submitfilter(request, setname, _("Filter modified"), tplname, ctx,
                            update=True, sc=sc)
            
    fset = sc.getscript(setname, format="fset")
    f = fset.getfilter(fname)
    form = build_filter_form_from_filter(request, fname, f)
    ctx = build_filter_ctx(ctx, form)
    ctx["oldname"] = fname
    return _render(request, tplname, ctx)

@login_required
def removefilter(request, setname, fname):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    fset = sc.getscript(setname, format="fset")
    if fset.removefilter(fname):
        sc.pushscript(fset.name, str(fset))
        return ajax_response(request, respmsg=_("Filter removed"))
    return ajax_response(request, "ko", respmsg=_("Failed to remove filter"))

@login_required
def savefs(request, name):
    if not request.POST.has_key("scriptcontent"):
        return
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.pushscript(name, request.POST["scriptcontent"])
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
                return ajax_response(request, 
                                     ajaxnav=True,
                                     url=form.cleaned_data["name"], 
                                     respmsg=_("Filters set created"))
        ctx["form"] = form
        ctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["form"] = FiltersSetForm()
    return _render(request, tplname, ctx)

@login_required
def remove_filters_set(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.deletescript(name)
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, respmsg=_("Filters set deleted"))

@login_required
def activate_filters_set(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.activatescript(name)
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, respmsg=_("Filters set activated"))

@login_required
def download_filters_set(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        script = sc.getscript(name)
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))

    resp = HttpResponse(script)
    resp["Content-Type"] = "text/plain"
    resp["Content-Length"] = len(script)
    resp["Content-Disposition"] = 'attachment; filename="%s.txt"' % name
    return resp

@login_required
def toggle_filter_state(request, setname, fname):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        fset = sc.getscript(setname, format="fset")
        if fset.is_filter_disabled(fname):
            ret = fset.enablefilter(fname)
            newstate = _("yes")
        else:
            ret = fset.disablefilter(fname)
            newstate = _("no")
        if not ret:
            pass
        sc.pushscript(setname, str(fset))
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    
    return ajax_response(request, respmsg=newstate)

def move_filter(request, setname, fname, direction):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        fset = sc.getscript(setname, format="fset")
        fset.movefilter(fname, direction)
        sc.pushscript(setname, str(fset))
    except (SieveClientError), e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, template="sievefilters/filters.html", fs=fset)

@login_required
def move_filter_up(request, setname, fname):
    return move_filter(request, setname, fname, "up")

@login_required
def move_filter_down(request, setname, fname):
    return move_filter(request, setname, fname, "down")
