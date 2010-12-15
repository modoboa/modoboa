# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _, ungettext
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction, IntegrityError

from modoboa import admin, userprefs
from models import *
from admin.permissions import *
from modoboa.lib import crypt_password
from modoboa.lib import _render, _render_to_string, _ctx_ok, \
    getctx, events, parameters
from modoboa.lib.models import Parameter
import copy

def good_domain(f):
    def dec(request, **kwargs):
        if request.user.is_superuser:
            return f(request, **kwargs)
        mb = Mailbox.objects.get(user=request.user.id)
        access = True
        if request.GET.has_key("domid"):
            dom_id = int(request.GET["domid"])
            if dom_id != mb.domain.id:
                access = False
        else:
            q = request.GET.copy()
            q["domid"] = mb.domain.id
            request.GET = q
        if access:
            return f(request, **kwargs)

        from django.conf import settings
        path = urlquote(request.get_full_path())
        login_url = settings.LOGIN_URL
        return HttpResponseRedirect("%s?next=%s" % (login_url, path))
    return dec

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
        dom.mbalias_counter = len(Alias.objects.filter(mboxes__domain__pk=dom.id))
    deloptions = {"keepdir" : _("Do not delete domain directory")}
    return render_domains_page(request, "domains",
                               domains=domains,
                               deloptions=deloptions)

@login_required
@permission_required("admin.add_domain")
def newdomain(request):
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
                    ctx = _ctx_ok(reverse(admin.views.domains))
                    messages.info(request, _("Domain created"), fail_silently=True)
                    return HttpResponse(simplejson.dumps(ctx), 
                                        mimetype="application/json")
                error = _("Failed to initialise domain, check permissions")
        content = _render_to_string(request, "admin/newdomain.html", {
                "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm()
    return _render(request, 'admin/newdomain.html', {
            "form" : form
            })

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
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
                ctx = _ctx_ok(reverse(admin.views.domains))
                messages.info(request, _("Domain modified"), fail_silently=True)
                return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
        content = _render_to_string(request, "admin/editdomain.html", {
                "domain" : domain, "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm(instance=domain) 
    return _render(request, 'admin/editdomain.html', {
            "domain" : domain, "form" : form
            })

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
        ctx = _ctx_ok("")
    else:
        ctx = getctx("ko", error=error)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

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
def newdomalias(request):
    if request.method == "POST":
        form = DomainAliasForm(request.POST)
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
                    ctx = _ctx_ok(reverse(admin.views.domaliases))
                    messages.info(request, _("Domain alias created"), fail_silently=True)
                    return HttpResponse(simplejson.dumps(ctx),
                                        mimetype="application/json")
        content = _render_to_string(request, "admin/newdomalias.html", {
                "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    form = DomainAliasForm()
    if not request.user.is_superuser:
        form.fields["target"].queryset = \
            Domain.objects.filter(mailbox__user__pk=request.user.id)
    if request.GET.has_key("domid"):
        form.fields["target"].initial = request.GET["domid"]
    return _render(request, 'admin/newdomalias.html', {
            "form" : form
            })

@login_required
@good_domain
@permission_required("admin.change_domainalias")
def editdomalias(request, alias_id):
    domalias = DomainAlias.objects.get(pk=alias_id)
    if request.method == "POST":
        form = DomainAliasForm(request.POST, instance=domalias)
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
                    ctx = _ctx_ok(reverse(admin.views.domaliases))
                    messages.info(request, _("Domain alias updated"), fail_silently=True)
                    return HttpResponse(simplejson.dumps(ctx),
                                        mimetype="application/json")
        content = _render_to_string(request, "admin/editdomalias.html", {
                "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
            
    form = DomainAliasForm(instance=domalias)
    return _render(request, 'admin/editdomalias.html', {
            "form" : form, "domalias" : domalias
            })

@login_required
@good_domain
@permission_required("admin.delete_domainalias")
def deldomalias(request):
    selection = request.GET["selection"].split(",")
    DomainAlias.objects.filter(id__in=selection).delete()
    msg = ungettext("Domain alias deleted", "Domain aliases deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return HttpResponse(simplejson.dumps(_ctx_ok("")), 
                        mimetype="application/json")

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
    mailboxes = Mailbox.objects.filter(domain=dom_id).exclude(user__id=request.user.id)
    return _render(request, 'admin/mailboxes_raw.html', {
            "mailboxes" : mailboxes
            })

@login_required
@good_domain
@permission_required("admin.add_mailbox")
def newmailbox(request):
    if request.method == "POST":
        form = MailboxForm(request.POST)
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
                ctx = _ctx_ok(reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)
                return HttpResponse(simplejson.dumps(ctx), 
                                    mimetype="application/json")
        content = _render_to_string(request, "admin/newmailbox.html", {
                "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = MailboxForm()
    if not request.user.is_superuser:
        form.fields["domain"].queryset = \
            Domain.objects.filter(mailbox__user__pk=request.user.id)
    if request.GET.has_key("domid"):
        form.fields["domain"].initial = request.GET["domid"]
    return _render(request, "admin/newmailbox.html", {
            "form" : form
            })

@login_required
@good_domain
@permission_required("admin.change_mailbox")
@transaction.commit_manually
def editmailbox(request, mbox_id=None):
    mb = Mailbox.objects.get(pk=mbox_id)
    if request.method == "POST":
        oldmb = copy.deepcopy(mb)
        form = MailboxForm(request.POST, instance=mb)
        error = None
        if form.is_valid():
            try:
                mb = form.save()
            except AdminError, inst:
                error = str(inst)
            else:
                if oldmb.rename_dir(mb.domain.name, mb.address):
                    transaction.commit()
                    events.raiseEvent("ModifyMailbox", mbox=mb, oldmbox=oldmb)
                    messages.info(request, _("Mailbox modified"),
                                  fail_silently=True)
                    ctx = _ctx_ok(reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)
                    return HttpResponse(simplejson.dumps(ctx),
                                        mimetype="application/json")
                error = _("Failed to rename mailbox, check permissions")                
        if error is not None:
            transaction.rollback()
        ctx = getctx("ko", content=_render_to_string(request, "admin/editmailbox.html", {
                    "mbox" : mb, "form" : form, "error" : error
                    }))
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = MailboxForm(instance=mb)
    form.fields['quota'].initial = mb.quota
    form.fields['enabled'].initial = mb.user.is_active
    form.fields['password1'].initial = "é"
    form.fields['password2'].initial = "é"
    return _render(request, 'admin/editmailbox.html', {
            "form" : form, "mbox" : mb
            })

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
        ctx = _ctx_ok("")
    else:
        ctx = getctx("ko", error=error)
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")

@login_required
@good_domain
@permission_required("admin.view_aliases")
def mbaliases(request):
    if request.GET.has_key("domid"):
        aliases = Alias.objects.filter(mboxes__domain__pk=request.GET["domid"]).distinct()
    elif request.GET.has_key("mbid"):
        aliases = Alias.objects.filter(mboxes__id=request.GET["mbid"]).distinct()
    else:
        aliases = Alias.objects.all()
    return render_domains_page(request, "mbaliases", aliases=aliases)

@login_required
@good_domain
@permission_required("admin.add_alias")
def newmbalias(request):    
    if request.method == "POST":
        form = AliasForm(request.POST)
        error = None
        if form.is_valid():
            try:
                alias = form.save()
            except IntegrityError:
                error = _("Alias with this name already exists")
            else:
                form.save_m2m()
                ctx = _ctx_ok(reverse(admin.views.mbaliases) )
                messages.info(request, _("Mailbox alias created"), fail_silently=True)
                return HttpResponse(simplejson.dumps(ctx),
                                    mimetype="application/json")
        content = _render_to_string(request, "admin/newmbalias.html", {
                "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    if request.GET.has_key("domid"):
        form = AliasForm(domain=Domain.objects.get(pk=request.GET["domid"]))
    else:
        form = AliasForm()
    if request.GET.has_key("mbid"):
        form.fields["mboxes"].initial = request.GET["mbid"]
    return _render(request, 'admin/newmbalias.html', {
             "form" : form, "noerrors" : True
            })

@login_required
@good_domain
@permission_required("admin.change_alias")
def editmbalias(request, alias_id):
    alias = Alias.objects.get(pk=alias_id)
    if request.method == "POST":
        form = AliasForm(request.POST, instance=alias)
        error = None
        if form.is_valid():
            try:
                alias = form.save()
            except IntegrityError:
                error = _("Alias with this name already exists")
            else:
                form.save_m2m()
                ctx = _ctx_ok(reverse(admin.views.mbaliases))
                messages.info(request, _("Mailbox alias modified"),
                              fail_silently=True)
                return HttpResponse(simplejson.dumps(ctx), 
                                    mimetype="application/json")
        content = _render_to_string(request, "admin/editmbalias.html", {
                "alias" : alias, "form" : form, "error" : error
                })
        ctx = getctx("ko", content=content)
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    form = AliasForm(instance=alias)
    return _render(request, 'admin/editmbalias.html', {
            "form" : form, "alias" : alias
            })

@login_required
@good_domain
@permission_required("admin.delete_alias")
def delmbalias(request):
    selection = request.GET["selection"].split(",")
    Alias.objects.filter(id__in=selection).delete()
    msg = ungettext("Alias deleted", "Aliases deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return HttpResponse(simplejson.dumps(_ctx_ok("")), 
                        mimetype="application/json")

@login_required
@permission_required("auth.view_permissions")
def permissions(request):
    permtables = []
    if request.user.is_superuser:
        permtables += [
            {"id" : "super_admins",
             "title" : _("Super administrators"),
             "content" : SuperAdminsPerms().get(request)}
            ]

    permtables += events.raiseQueryEvent("PermsGetTables", user=request.user)

    permtables += [
        {"id" : "domain_admins",
         "title" : _("Domain administrators"),
         "content" : DomainAdminsPerms().get(request)}
        ]

    return _render(request, 'admin/permissions.html', {
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
    ctx = _ctx_ok(reverse(admin.views.permissions))
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")

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
def viewparameters(request):
    apps = sorted(parameters._params.keys())
    gparams = []
    for app in apps:
        tmp = {"name" : app, "params" : []}
        for p in sorted(parameters._params[app]['A']):
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

    return _render(request, 'admin/parameters.html', {
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
    ctx = getctx("ok")
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewextensions(request):
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
    return _render(request, 'admin/extensions.html', {
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
