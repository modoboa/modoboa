# coding: utf-8
from sievelib.managesieve import Error
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import parameters
from modoboa.lib.webutils import _render, _render_to_string, _render_error, \
    ajax_response, ajax_simple_response
from modoboa.lib.decorators import needs_mailbox
from modoboa.lib.connections import ConnectionError
from modoboa.auth.lib import get_password
from lib import *
from forms import *
from templatetags.sfilters_tags import fset_menu

@login_required
@needs_mailbox()
def index(request, tplname="sievefilters/index.html"):
    from modoboa.extensions.webmail.imaputils import get_imapconnector

    try:
        sc = SieveClient(user=request.user.username, 
                         password=request.session["password"])
    except ConnectionError, e:
        return _render_error(request, user_context={"error" : e})
    
    try:
        active_script, scripts = sc.listscripts()
    except Error, e:
        return _render_error(request, user_context={"error" : e})

    if active_script is None:
        active_script = ""
        default_script = "%s/" % scripts[0] if len(scripts) else ""
    else:
        default_script = "%s/" % active_script
    return _render(request, tplname, {
            "selection" : "user",
            "active_script" : active_script,
            "default_script" : default_script,
            "scripts" : sorted(scripts),
            "hdelimiter": get_imapconnector(request).hdelimiter
            })

@login_required
@needs_mailbox()
def get_templates(request, ftype):
    if ftype == "condition":
        return ajax_simple_response(FilterForm([], [], request).cond_templates)
    return ajax_simple_response(FilterForm([], [], request).action_templates)

@login_required
@needs_mailbox()
def getfs(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    editormode = parameters.get_user(request.user, "EDITOR_MODE")
    error = None
    try:
        content = sc.getscript(name, format=editormode)
    except SieveClientError, e:
        error = str(e)
    else:
        if content is None:
            error = _("Failed to retrieve filters set")

    if error is not None:
        return ajax_response(request, "ko", respmsg=error)

    if editormode == "raw":
        htmlcontent =  render_to_string("sievefilters/rawfilter.html", dict(
                name=name, scriptcontent=content
                ))
    else:
        htmlcontent = render_to_string("sievefilters/guieditor.html", dict(
                fs=content
                ))

    menu = '<ul id="fsetmenu" class="nav nav-list"><li class="nav-header">%s</li>%s</ul>' % \
            (_("Actions"), fset_menu(editormode, name))
    resp = dict(status="ok", menu=menu, content=htmlcontent)
    return ajax_simple_response(resp)

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
        match_type = form.cleaned_data["match_type"]
        if match_type == "all":
            match_type = "anyof"
            conditions = [("true",)]
        fltname = form.cleaned_data["name"].encode("utf-8")
        if not update:
            fset.addfilter(fltname, conditions, actions,
                           match_type)
        else:
            oldname = request.POST["oldname"].encode("utf-8")
            fset.updatefilter(
                oldname, fltname, conditions, actions, match_type
            )
        try:
            sc.pushscript(fset.name, str(fset))
        except SieveClientError as e:
            return ajax_response(request, "ko", respmsg=str(e))
        return ajax_response(request, respmsg=okmsg, ajaxnav=True)
    tplctx = build_filter_ctx(tplctx, form)
    return ajax_response(request, status="ko", template=tplname, **tplctx)

@login_required
@needs_mailbox()
def newfilter(request, setname, tplname="sievefilters/filter.html"):
    ctx = dict(
        title=_("New filter"),
        formid="filterform",
        action=reverse(newfilter, args=[setname]),
        action_label=_("Create"),
        action_classes="submit"
        )
    if request.method == "POST":
        return submitfilter(request, setname, _("Filter created"), tplname, ctx)

    conds = [("Subject", "contains", "")]
    actions = [("fileinto", "")]
    form = FilterForm(conds, actions, request)
    ctx = build_filter_ctx(ctx, form)
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def editfilter(request, setname, fname, tplname="sievefilters/filter.html"):
    ctx = dict(
        title=_("Edit filter"),
        formid="filterform",
        action=reverse(editfilter, args=[setname, fname]),
        action_label=_("Update"),
        action_classes="submit"
        )
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    if request.method == "POST":
        return submitfilter(request, setname, _("Filter modified"), tplname, ctx,
                            update=True, sc=sc)
            
    fset = sc.getscript(setname, format="fset")
    if type(fname) is unicode:
        fname = fname.encode("utf-8")
    f = fset.getfilter(fname)
    form = build_filter_form_from_filter(request, fname, f)
    ctx = build_filter_ctx(ctx, form)
    ctx["oldname"] = fname
    ctx["hidestyle"] = "none" \
        if form.fields["match_type"].initial == "all" else "block"
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def removefilter(request, setname, fname):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    fset = sc.getscript(setname, format="fset")
    if fset.removefilter(fname.encode("utf-8")):
        sc.pushscript(fset.name, str(fset))
        return ajax_response(request, respmsg=_("Filter removed"))
    return ajax_response(request, "ko", respmsg=_("Failed to remove filter"))

@login_required
@needs_mailbox()
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
@needs_mailbox()
def new_filters_set(request, tplname="common/generic_modal_form.html"):
    ctx = {"title" : _("Create a new filters set"),
           "formid" : "newfiltersset",
           "action_label" : _("Create"),
           "action_classes" : "submit",
           "action" : reverse(new_filters_set),
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
                return ajax_simple_response({
                    "status": "ok", 
                    "url": form.cleaned_data["name"],
                    "active": form.cleaned_data["active"],
                    "respmsg": _("Filters set created")
                })

        ctx["form"] = form
        ctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["form"] = FiltersSetForm()
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def remove_filters_set(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.deletescript(name)
    except SieveClientError, e:
        return ajax_simple_response(dict(status="ko", respmsg=str(e)))
    acs, scripts = sc.listscripts()
    return ajax_simple_response(dict(
            status="ok", respmsg=_("Filters set deleted"), newfs=acs
            ))

@login_required
@needs_mailbox()
def activate_filters_set(request, name):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        sc.activatescript(name)
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, respmsg=_("Filters set activated"))

@login_required
@needs_mailbox()
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
@needs_mailbox()
def toggle_filter_state(request, setname, fname):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    if type(fname) is unicode:
        fname = fname.encode("utf-8")
    try:
        fset = sc.getscript(setname, format="fset")
        if fset.is_filter_disabled(fname):
            ret = fset.enablefilter(fname)
            newstate = _("yes")
            color = "green"
        else:
            ret = fset.disablefilter(fname)
            newstate = _("no")
            color = "red"
        if not ret:
            pass
        sc.pushscript(setname, str(fset))
    except SieveClientError, e:
        return ajax_response(request, "ko", respmsg=str(e))
    
    return ajax_simple_response({
            "status" : "ok",
            "label" : newstate,
            "color" : color
            })

def move_filter(request, setname, fname, direction):
    sc = SieveClient(user=request.user.username, 
                     password=request.session["password"])
    try:
        fset = sc.getscript(setname, format="fset")
        fset.movefilter(fname.encode("utf-8"), direction)
        sc.pushscript(setname, str(fset))
    except (SieveClientError), e:
        return ajax_response(request, "ko", respmsg=str(e))
    return ajax_response(request, template="sievefilters/guieditor.html", fs=fset)

@login_required
@needs_mailbox()
def move_filter_up(request, setname, fname):
    return move_filter(request, setname, fname, "up")

@login_required
@needs_mailbox()
def move_filter_down(request, setname, fname):
    return move_filter(request, setname, fname, "down")
