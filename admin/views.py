# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _, ungettext
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction, IntegrityError

from lib import *
from modoboa import admin, userprefs
from models import *
from admin.permissions import *
from modoboa.lib import crypt_password
from modoboa.lib import _render, ajax_response, ajax_simple_response, \
    getctx, events, parameters
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.models import Parameter
import copy

def render_domains_page(request, page, **kwargs):
    template = "admin/%s.html" % page
    if request.GET.has_key("domid"):
        kwargs["domid"] = request.GET["domid"]
    else:
        kwargs["domid"] = ""
    kwargs["selection"] = page
    return _render(request, template, kwargs)

@login_required
def domains(request):
    if not request.user.has_perm("admin.view_domains"):
        if request.user.has_perm("admin.view_mailboxes"):
            return HttpResponseRedirect(reverse(mailboxes))

        return HttpResponseRedirect(reverse(userprefs.views.preferences))
    
    domains = Domain.objects.all()
    for dom in domains:
        dom.mbalias_counter = len(Alias.objects.filter(domain=dom.id))
    deloptions = {"keepdir" : _("Do not delete domain directory")}
    return render_domains_page(request, "domains",
                               domains=domains,
                               deloptions=deloptions)

@login_required
@permission_required("admin.add_domain")
def newdomain(request, tplname="admin/adminform.html"):
    commonctx = {"title" : _("New domain"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newdomain),
                 "formid" : "domform"}
    if request.method == "POST":
        form = DomainForm(request.POST)
        error = None
        if form.is_valid():
            if Domain.objects.filter(name=request.POST["name"]):
                error = _("Domain with this name already defined")
            else:
                domain = form.save(commit=False)
                if domain.create_dir():
                    form.save()
                    events.raiseEvent("CreateDomain", dom=domain)
                    messages.info(request, _("Domain created"), fail_silently=True)
                    return ajax_response(request, url=reverse(admin.views.domains))

                error = _("Failed to initialise domain, check permissions")
        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = DomainForm()
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id, tplname="admin/adminform.html"):
    domain = Domain.objects.get(pk=dom_id)
    commonctx = {"title" : _("Domain editing"),
                 "submit_label" : _("Update"),
                 "action" : reverse(editdomain, args=[dom_id]),
                 "formid" : "domform"}
    olddomain = copy.deepcopy(domain)
    if request.method == "POST":
        form = DomainForm(request.POST, instance=domain)
        error = None
        if form.is_valid():
            if domain.name != olddomain.name:
                if Domain.objects.filter(name=domain.name):
                    error = _("Domain with this name already defined")
                else:
                    if not olddomain.rename_dir(domain.name):
                        error = _("Failed to rename domain, check permissions")
            if not error:
                form.save()
                messages.info(request, _("Domain modified"), fail_silently=True)
                return ajax_response(request, url=reverse(admin.views.domains))

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = DomainForm(instance=domain)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.delete_domain")
def deldomain(request):
    selection = request.GET["selection"].split(",")
    error = None
    if request.user.id != 1:
        mb = Mailbox.objects.get(user__id=request.user.id)
        if str(dom.id) in selection:
            error = _("You can't delete your own domain")
    if error is None:
        if request.GET.has_key("keepdir") and request.GET["keepdir"] == "true":
            keepdir = True
        else:
            keepdir = False
        for dom in Domain.objects.filter(id__in=selection):
            events.raiseEvent("DeleteDomain", dom=dom)
            dom.delete(keepdir=keepdir)
        msg = ungettext("Domain deleted", "Domains deleted", len(selection))
        messages.info(request, msg, fail_silently=True)
        return ajax_response(request)
    return ajax_response(request, status="ko", error=error)

@login_required
@permission_required("admin.view_domaliases")
def domaliases(request):
    if request.GET.has_key("domid"):
        domain = Domain.objects.get(pk=request.GET["domid"])
        domaliases = DomainAlias.objects.filter(target=request.GET["domid"])
    else:
        domain = None
        domaliases = DomainAlias.objects.all()
    return render_domains_page(request, "domaliases",
                               domaliases=domaliases, domain=domain)

@login_required
@good_domain
@permission_required("admin.add_domainalias")
def newdomalias(request, tplname="admin/adminform.html"):
    commonctx = {"title" : _("New domain alias"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newdomalias),
                 "formid" : "domaliasform"}
    if request.method == "POST":
        form = DomainAliasForm(request.user, request.POST)
        error = None
        if form.is_valid():
            domalias = form.save(commit=False)
            if Domain.objects.filter(name=domalias.name):
                error = _("A domain with this name already exists")
            else:
                try:
                    domalias.save()
                except IntegrityError:
                    error = _("Alias with this name already exists")
                else:
                    messages.info(request, _("Domain alias created"), fail_silently=True)
                    return ajax_response(request, url=reverse(admin.views.domaliases))

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = DomainAliasForm(request.user)
    if request.GET.has_key("domid"):
        form.fields["target"].initial = request.GET["domid"]
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.change_domainalias")
def editdomalias(request, alias_id, tplname="admin/adminform.html"):
    domalias = DomainAlias.objects.get(pk=alias_id)
    commonctx = {"title" : _("Domain alias editing"),
                 "submit_label" : _("Update"),
                 "action" : reverse(editdomalias, args=[alias_id]),
                 "formid" : "domaliasform"}
    if request.method == "POST":
        form = DomainAliasForm(request.user, request.POST, instance=domalias)
        error = None
        if form.is_valid():
            ndomalias = form.save(commit=False)
            if Domain.objects.filter(name=ndomalias.name):
                error = _("A domain with this name already exists")
            else:
                try:
                    ndomalias.save()
                except IntegrityError:
                    error = _("Alias with this name already exists")
                else:
                    messages.info(request, _("Domain alias updated"), fail_silently=True)
                    return ajax_response(request, url=reverse(admin.views.domaliases))
        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)
            
    form = DomainAliasForm(request.user, instance=domalias)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.delete_domainalias")
def deldomalias(request):
    selection = request.GET["selection"].split(",")
    DomainAlias.objects.filter(id__in=selection).delete()
    msg = ungettext("Domain alias deleted", "Domain aliases deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def mailboxes(request):
    if request.GET.has_key("domid"):
        domain = Domain.objects.get(pk=request.GET["domid"])
        mboxes = Mailbox.objects.filter(domain=domain.id)
    else:
        mboxes = Mailbox.objects.all()
        domain = None
    deloptions = {"keepdir" : _("Do not delete mailbox directory")}
    return render_domains_page(request, "mailboxes",
                               mailboxes=mboxes, domain=domain, deloptions=deloptions)

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def mailboxes_raw(request, dom_id=None):
    target = request.GET.has_key("target") and request.GET["target"] or "permissions"
    if target == "permissions":
        mailboxes = Mailbox.objects.filter(domain=dom_id).exclude(user__id=request.user.id)
    else:
        mailboxes = Mailbox.objects.filter(domain=dom_id)
    return _render(request, 'admin/mailboxes_raw.html', {
            "mailboxes" : mailboxes,
            "target" : target
            })

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def mailboxes_search(request):
    if request.method != "POST":
        return
    addr = EmailAddress(request.POST["search"])
    local_part, domain = split_mailbox(request.POST["search"])
    query = Q(address__startswith=local_part)
    if domain is not None and domain != "":
        query &= Q(domain__name__startswith=domain)
    if request.GET.has_key("domid"):
        query = Q(domain=request.GET["domid"]) & query
    mboxes = Mailbox.objects.filter(query)
    result = map(lambda mb: mb.full_address, mboxes)
    return ajax_simple_response(result)

@login_required
@good_domain
@permission_required("admin.add_mailbox")
def newmailbox(request, tplname="admin/adminform.html"):
    commonctx = {"title" : _("New mailbox"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newmailbox),
                 "formid" : "mboxform"}
    if request.method == "POST":
        form = MailboxForm(request.user, request.POST)
        error = None
        if form.is_valid():
            try:
                mb = form.save()
            except AdminError as e:
                error = str(e)
            else:
                events.raiseEvent("CreateMailbox", mbox=mb)
                messages.info(request, _("Mailbox created"),
                              fail_silently=True)
                return ajax_response(request, url=reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = MailboxForm(request.user)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.change_mailbox")
def editmailbox(request, mbox_id=None, tplname="admin/adminform.html"):
    mb = Mailbox.objects.get(pk=mbox_id)
    commonctx = {"title" : _("Mailbox editing"),
                 "submit_label" : _("Create"),
                 "action" : reverse(editmailbox, args=[mbox_id]),
                 "formid" : "mboxform"}
    if request.method == "POST":
        oldmb = copy.deepcopy(mb)
        form = MailboxForm(request.user, request.POST, instance=mb)
        error = None
        if form.is_valid():
            try:
                mb = form.save(commit=False)
            except AdminError, inst:
                error = str(inst)
            else:
                if oldmb.rename_dir(mb.domain.name, mb.address):
                    form.commit_save(mb)
                    events.raiseEvent("ModifyMailbox", mbox=mb, oldmbox=oldmb)
                    messages.info(request, _("Mailbox modified"),
                                  fail_silently=True)
                    return ajax_response(request, url=reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)
                error = _("Failed to rename mailbox, check permissions")                

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = MailboxForm(request.user, instance=mb)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.delete_mailbox")
def delmailbox(request):
    selection = request.GET["selection"].split(",")
    error = None
    if not request.user.is_superuser:
        mb = Mailbox.objects.get(user__pk=request.user.id)
        if str(mb.id) in selection:
            error = _("You can't delete your own mailbox")

    if error is None:
        if request.GET.has_key("keepdir") and request.GET["keepdir"] == "true":
            keepdir = True
        else:
            keepdir = False
        for mb in Mailbox.objects.filter(id__in=selection):
            events.raiseEvent("DeleteMailbox", mbox=mb)
            mb.delete(keepdir=keepdir)
        msg = ungettext("Mailbox deleted", "Mailboxes deleted", len(selection))
        messages.info(request, msg, fail_silently=True)
        return ajax_response(request)

    return ajax_response(request, status="ko", error=error)

@login_required
@good_domain
@permission_required("admin.view_aliases")
def mbaliases(request):
    if request.GET.has_key("domid"):
        aliases = Alias.objects.filter(domain=request.GET["domid"])
    elif request.GET.has_key("mbid"):
        aliases = Alias.objects.filter(mboxes__id=request.GET["mbid"]).distinct()
    else:
        aliases = Alias.objects.all()
    if not request.user.is_superuser:
        usermb = Mailbox.objects.get(user=request.user.id)
        for al in aliases:
            al.ui_disabled = False
            for mb in al.mboxes.all():
                if mb.domain.id != usermb.domain.id:
                    al.ui_disabled = True
                    break
    return render_domains_page(request, "mbaliases", aliases=aliases)

def _validate_mbalias(request, form, successmsg, tplname, commonctx):
    """Mailbox alias validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        try:
            if not request.POST.has_key("targets"):
                raise AdminError(_("No target defined"))
            form.set_targets(request.user, request.POST.getlist("targets"))
            try:
                alias = form.save()
            except IntegrityError:
                raise AdminError(_("Alias with this name already exists"))
            
            messages.info(request, successmsg, fail_silently=True)
            return ajax_response(request, url=reverse(admin.views.mbaliases))
        except AdminError, e:
            error = str(e)

    if request.POST.has_key("targets"):
        targets = request.POST.getlist("targets")
        commonctx["targets"] = targets[:-1]

    commonctx["form"] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@good_domain
@permission_required("admin.add_alias")
def newmbalias(request, tplname="admin/mbaliasform.html"):
    commonctx = {"title" : _("New mailbox alias"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newmbalias),
                 "formid" : "mbaliasform"}
    if request.method == "POST":
        form = AliasForm(request.user, request.POST)
        return _validate_mbalias(request, form, _("Mailbox alias created"),
                                 tplname, commonctx)

    form = AliasForm(request.user)
    commonctx["form"] = form
    commonctx["noerrors"] = True
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.change_alias")
def editmbalias(request, alias_id, tplname="admin/mbaliasform.html"):
    alias = Alias.objects.get(pk=alias_id)
    commonctx = {"title" : _("Mailbox alias editing"),
                 "submit_label" : _("Update"),
                 "action" : reverse(editmbalias, args=[alias.id]),
                 "formid" : "mbaliasform"}
    if request.method == "POST":
        form = AliasForm(request.user, request.POST, instance=alias)
        return _validate_mbalias(request, form, _("Mailbox alias modified"),
                                 tplname, commonctx)

    form = AliasForm(request.user, instance=alias)
    commonctx["form"] = form
    commonctx["targets"] = alias.get_targets()
    return _render(request, tplname, commonctx)

@login_required
@good_domain
@permission_required("admin.delete_alias")
def delmbalias(request):
    selection = request.GET["selection"].split(",")
    Alias.objects.filter(id__in=selection).delete()
    msg = ungettext("Alias deleted", "Aliases deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@permission_required("auth.view_permissions")
def permissions(request, tplname='admin/permissions.html'):
    permtables = []
    if request.user.is_superuser:
        permtables += [
            {"id" : "super_admins",
             "title" : _("Super administrators"),
             "rel" : "300 140",
             "content" : SuperAdminsPerms().get(request)}
            ]

    permtables += events.raiseQueryEvent("PermsGetTables", user=request.user)

    permtables += [
        {"id" : "domain_admins",
         "title" : _("Domain administrators"),
         "rel" : "300 180",
         "content" : DomainAdminsPerms().get(request)}
        ]

    return _render(request, tplname, {
            "permtables" : permtables
            })

@login_required
@permission_required("auth.view_permissions")
def add_permission(request):
    role = request.method == "GET" and request.GET["role"] or request.POST["role"]
    pclass = get_perms_class(request.user, role)
    if pclass is None:
        messages.error(request, _("Permission denied!"), 
                       fail_silently=True)
    else:
        pobj = pclass()
        if request.method == "GET":
            return pobj.get_add_form(request)
        status, data = pobj.add(request)
        if not status:
            return HttpResponse(simplejson.dumps(data), mimetype="application/json")
        messages.info(request, _("Permission added."), 
                      fail_silently=True)
    return ajax_response(request, url=reverse(admin.views.permissions))

@login_required
def delete_permissions(request):
    pclass = get_perms_class(request.user, request.GET["role"])
    if pclass is None:
        ctx = getctx("ko", message=_("Permission denied!"))
    else:
        selection = request.GET["selection"].split(",")
        pobj = pclass()
        pobj.delete(selection)
        ctx = getctx("ok", content=pobj.get(request), 
                     message=_("Permissions removed"))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewparameters(request, tplname='admin/parameters.html'):
    apps = sorted(parameters._params.keys())
    gparams = []
    for app in apps:
        tmp = {"name" : app, "params" : []}
        for p in parameters._params_order[app]['A']:

            param_def = parameters._params[app]['A'][p]
            newdef = {"name" : p, 
                      "value" : parameters.get_admin(p, app=app),
                      "help" : param_def["help"],
                      "default" : param_def["deflt"],
                      "type" : param_def["type"]}
            if "values" in param_def.keys():
                newdef["values"] = param_def["values"]
            tmp["params"] += [newdef]
        gparams += [tmp]

    return _render(request, tplname, {
            "gparams" : gparams
            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveparameters(request):
    for pname, v in request.POST.iteritems():
        if pname == "update":
            continue
        app, name = pname.split('.')
        parameters.save_admin(name, v, app=app)
    return ajax_response(request)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewextensions(request, tplname='admin/extensions.html'):
    from modoboa.extensions import list_extensions
    from modoboa.lib import tables
    
    class ExtensionsTable(tables.Table):
        idkey = "id"
        selection = tables.SelectionColumn("selection", width="4%", first=True)
        _1_name = tables.Column("name", label=_("Name"), width="15%")
        _2_version = tables.Column("version", label=_("Version"), width="6%")
        _3_descr = tables.Column("description", label=_("Description"))
        
    exts = list_extensions()
    for ext in exts:
        try:
            dbext = Extension.objects.get(name=ext["id"])
            ext["selection"] = dbext.enabled
        except Extension.DoesNotExist:
            dbext = Extension()
            dbext.name = ext["id"]
            dbext.enabled = False
            dbext.save()
            ext["selection"] = False
            
    tbl = ExtensionsTable(exts)
    return _render(request, tplname, {
            "extensions" : tbl.render(request)
            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveextensions(request):
    from modoboa import extensions

    actived_exts = Extension.objects.filter(enabled=True)
    found = []
    for k, v in request.POST.iteritems():
        if k.startswith("select_"):
            parts = k.split("_", 1)
            dbext = Extension.objects.get(name=parts[1])            
            if not dbext in actived_exts:
                dbext.on()
                dbext.enabled = True
                dbext.save()
            else:
                found += [dbext]
    for ext in actived_exts:
        if not ext in found:
            ext.off()
            ext.enabled = False
            ext.save()
    messages.info(request, _("Modifications applied."), fail_silently=True)
    return HttpResponseRedirect(reverse(admin.views.viewextensions))
