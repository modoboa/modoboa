# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.core import serializers
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages

from modoboa import admin, userprefs
from modoboa.admin.models import *
from forms import MailboxForm, DomainForm, AliasForm, PermissionForm
from modoboa.lib.authbackends import crypt_password
from modoboa.lib import _render, _ctx_ok, _ctx_ko, getctx
from modoboa.lib import events, parameters
from modoboa.lib.models import Parameter
import string
import copy
import pwd

def is_superuser(user):
    if not user.is_superuser:
        user.message_set.create(message=_("Permission denied."))
        return False
    return True

def good_domain(f):
    def dec(request, dom_id, **kwargs):
        if request.user.is_superuser:
            return f(request, dom_id, **kwargs)
        mb = Mailbox.objects.get(user=request.user.id)
        if isinstance(dom_id, str) or isinstance(dom_id, unicode):
            dom_id = string.atoi(dom_id)
        if dom_id == mb.domain.id:
            return f(request, dom_id, **kwargs)

        from django.conf import settings
        path = urlquote(request.get_full_path())
        login_url = settings.LOGIN_URL
        return HttpResponseRedirect("%s?next=%s" % (login_url, path))
    return dec

@login_required
def domains(request):
    if not request.user.has_perm("admin.view_domains"):
        print "redirect"
        if request.user.has_perm("admin.view_mailboxes"):
            mb = Mailbox.objects.get(user=request.user.id)
            return mailboxes(request, dom_id=mb.domain.id)

        return HttpResponseRedirect(reverse(userprefs.views.preferences))
    
    domains = Domain.objects.all()
    counters = {}
    for dom in domains:
        dom.mboxcounter = len(dom.mailbox_set.all())
    return _render(request, 'admin/domains.html', {
            "domains" : domains, "counters" : counters
            })

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
                    return HttpResponse(simplejson.dumps(ctx), 
                                        mimetype="application/json")
                error = _("Failed to initialise domain, check permissions")
        ctx = _ctx_ko("admin/newdomain.html", {
                "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm()
    return render_to_response('admin/newdomain.html', {
            "form" : form
            })

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
    if request.method == "POST":
        form = DomainForm(request.POST, instance=domain)
        error = None
        if form.is_valid():
            if domain.name != request.POST["name"]:
                if Domain.objects.filter(name=request.POST["name"]):
                    error = _("Domain with this name already defined")
                else:
                    if not domain.rename_dir(request.POST["name"]):
                        error = _("Failed to rename domain, check permissions")
            if not error:
                form.save()
                ctx = _ctx_ok(reverse(admin.views.domains))
                return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
        ctx = _ctx_ko("admin/editdomain.html", {
                "domain" : domain, "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm(instance=domain) 
    return render_to_response('admin/editdomain.html', {
            "domain" : domain, "form" : form
            })

@login_required
@permission_required("admin.delete_domain")
def deldomain(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
    events.raiseEvent("DeleteDomain", dom=domain)
    domain.delete_dir()
    domain.delete()
    return HttpResponseRedirect('/modoboa/admin/')

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def mailboxes(request, dom_id=None):
    domain = Domain.objects.get(pk=dom_id)
    mailboxes = Mailbox.objects.filter(domain=dom_id)
    return _render(request, 'admin/mailboxes.html', {
            "mailboxes" : mailboxes, "domain" : domain
            })

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def mailboxes_raw(request, dom_id=None):
    mailboxes = Mailbox.objects.filter(domain=dom_id)
    return _render(request, 'admin/mailboxes_raw.html', {
            "mailboxes" : mailboxes
            })

@login_required
@good_domain
@permission_required("admin.add_mailbox")
def newmailbox(request, dom_id=None):
    domain = Domain.objects.get(pk=dom_id)
    if request.method == "POST":
        form = MailboxForm(request.POST)
        error = None
        if form.is_valid():
            if Mailbox.objects.filter(address=request.POST["address"],
                                      domain=dom_id):
                error = _("Mailbox with this address already exists")
            else:
                mb = form.save(commit=False)
                if mb.create_dir(domain):
                    from django.conf import settings

                    user = User()
                    user.username = user.email = "%s@%s" % (mb.address, domain.name)
                    user.set_unusable_password()
                    user.is_active = request.POST.has_key("enabled") \
                        and True or False
                    try:
                        fname, lname = mb.name.split()
                    except ValueError:
                        fname = mb.name
                        lname = ""
                    user.first_name = fname
                    user.last_name = lname
                    user.save()
                    mb.user = user
                 
                    mb.password = crypt_password(request.POST["password1"])
                    
                    mb.uid = pwd.getpwnam(parameters.get_admin("VIRTUAL_UID")).pw_uid
                    mb.gid = pwd.getpwnam(parameters.get_admin("VIRTUAL_GID")).pw_gid
                    mb.domain = domain
                    mb.quota = request.POST["quota"]
                    if not mb.quota:
                        mb.quota = domain.quota
                    mb.full_address = "%s@%s" % (mb.address, domain.name)
                    mb.save()
                    
                    events.raiseEvent("CreateMailbox", mbox=mb)

                    messages.info(request, _("Mailbox created."), 
                                  fail_silently=True)
                    ctx = _ctx_ok(reverse(admin.views.mailboxes, args=[domain.id]))
                    return HttpResponse(simplejson.dumps(ctx), 
                                        mimetype="application/json")
            error = _("Failed to initialise mailbox, check permissions")
        ctx = _ctx_ko("admin/newmailbox.html", {
                "form" : form, "domain" : domain, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = MailboxForm()
    return _render(request, "admin/newmailbox.html", {
            "domain" : domain, "form" : form
            })

@login_required
@good_domain
@permission_required("admin.change_mailbox")
def editmailbox(request, dom_id, mbox_id=None):
    mb = Mailbox.objects.get(pk=mbox_id)
    if request.method == "POST":
        oldmb = copy.deepcopy(mb)
        form = MailboxForm(request.POST, instance=mb)
        error = None
        if form.is_valid():
            if mb.address != request.POST["address"]:
                if Mailbox.objects.filter(address=request.POST["address"],
                                          domain=dom_id):
                    error = _("Mailbox with this address already exists")
                else:
                    if not mb.rename_dir(mb.domain.name, request.POST["address"]):
                        error = _("Failed to rename mailbox, check permissions")
            if not error:
                mb = form.save(commit=False)
                mb.user.is_active = request.POST.has_key("enabled") \
                    and request.POST["enabled"] or False
                mb.user.save()

                if request.POST["password1"] != u"é":
                    mb.password = crypt_password(request.POST["password1"])
                mb.quota = request.POST["quota"]
                if not mb.quota:
                    mb.quota = mb.domain.quota
                mb.full_address = "%s@%s" % (mb.address, mb.domain.name)
                mb.save()
                events.raiseEvent("ModifyMailbox", mbox=mb, oldmbox=oldmb)
                ctx = _ctx_ok(reverse(admin.views.mailboxes, args=[dom_id]))
                return HttpResponse(simplejson.dumps(ctx),
                                    mimetype="application/json")
        ctx = _ctx_ko("admin/editmailbox.html", {
                "mbox" : mb, "form" : form, "error" : error
                })
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
def delmailbox(request, dom_id, mbox_id=None):
    mb = Mailbox.objects.get(pk=mbox_id)
    events.raiseEvent("DeleteMailbox", mbox=mb)
    if not request.GET.has_key("keepdir") or request.GET["keepdir"] != "true":
        mb.delete_dir()
    mb.user.delete()
    mb.delete()
    ctx = _ctx_ok("");
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")
#     return HttpResponseRedirect(reverse(admin.views.mailboxes, 
#                                         args=[dom_id]))

@login_required
@good_domain
@permission_required("admin.view_aliases")
def aliases(request, dom_id=None, mbox_id=None):
    domain = Domain.objects.get(pk=dom_id)
    if not mbox_id:
        aliases = Alias.objects.filter(mboxes__domain__id=dom_id).distinct()
    else:
        aliases = Alias.objects.filter(mboxes__id=mbox_id)
    return _render(request, 'admin/aliases.html', {
            "aliases" : aliases, "domain" : domain
            })

@login_required
@good_domain
@permission_required("admin.add_alias")
def newalias(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
    if request.method == "POST":
        form = AliasForm(request.POST, domain=domain)
        error = None
        if form.is_valid():
            if Alias.objects.filter(address=request.POST["address"]):
                error = _("Alias with this name already exists")
            else:
                alias = form.save(commit=False)
                alias.full_address = "%s@%s" % (alias.address, domain.name)
                alias.save()
                form.save_m2m()
                ctx = _ctx_ok(reverse(admin.views.aliases, args=[dom_id]))
                return HttpResponse(simplejson.dumps(ctx),
                                    mimetype="application/json")
        ctx = _ctx_ko("admin/newalias.html", {
                "domain" : dom_id, "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = AliasForm(domain=domain)
    return render_to_response('admin/newalias.html', {
            "domain" : dom_id, "form" : form, "noerrors" : True
            })

@login_required
@good_domain
@permission_required("admin.change_alias")
def editalias(request, dom_id, alias_id):
    alias = Alias.objects.get(pk=alias_id)
    if request.method == "POST":
        form = AliasForm(request.POST, instance=alias)
        error = None
        if form.is_valid():
            if alias.address != request.POST["address"] \
                    and Alias.objects.filter(address=request.POST["address"]):
                error = _("Alias with this name already exists")
            else:
                domain = Domain.objects.get(pk=dom_id)
                alias = form.save(commit=False)
                alias.full_address = "%s@%s" % (alias.address, 
                                                domain.name)
                alias.save()
                form.save_m2m()
                ctx = _ctx_ok(reverse(admin.views.aliases, args=[dom_id]))
                return HttpResponse(simplejson.dumps(ctx), 
                                    mimetype="application/json")
        ctx = _ctx_ko("admin/editalias.html", {
                "alias" : alias, "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    form = AliasForm(instance=alias)
    return _render(request, 'admin/editalias.html', {
            "form" : form, "alias" : alias, "domain" : dom_id
            })

@login_required
@good_domain
@permission_required("admin.delete_alias")
def delalias(request, dom_id, alias_id):
    alias = Alias.objects.get(pk=alias_id)
    alias.delete()
    return HttpResponseRedirect(reverse(admin.views.aliases, 
                                        args=[dom_id]))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def settings(request):
    admins = User.objects.filter(is_superuser=True)
    domadmins = Mailbox.objects.filter(user__groups__name="DomainAdmins")
    return _render(request, 'admin/permissions.html', {
            "admins" : admins, "domadmins" : domadmins
            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def addpermission(request):
    if request.method == "POST":
        form = PermissionForm(request.POST)
        if request.POST.has_key('user'):
            mboxid = request.POST['user']
            form.fields["user"].choices = \
                [(mboxid, Mailbox.objects.get(pk=mboxid)),]
        if form.is_valid():
            mb = Mailbox.objects.get(pk=request.POST["user"])
            if request.POST["role"] == "SuperAdmins":
                mb.user.is_superuser = True
                mb.user.groups.clear()
            else:
                mb.user.is_superuser = False
                mb.user.groups.add(Group.objects.get(name=request.POST["role"]))
            mb.user.save()
            ctx = _ctx_ok(reverse(admin.views.settings))
            return HttpResponse(simplejson.dumps(ctx), 
                                mimetype="application/json")
        ctx = _ctx_ko("admin/addpermission.html", {
                "form" : form
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    
    form = PermissionForm()
    return _render(request, 'admin/addpermission.html', {
            "form" : form
            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def deletepermission(request, mbox_id, group):
    if group == "SuperAdmins":
        user = User.objects.get(pk=mbox_id)
        if user.username == "admin":
            messages.error(request, _("admin is intouchable!!"), fail_silently=True)
        else:
            user.is_superuser = False
            user.save()
    else:
        mbox = Mailbox.objects.get(pk=mbox_id)
        grp = Group.objects.get(name=group)
        mbox.user.groups.remove(grp)
        mbox.user.save()
    return HttpResponseRedirect(reverse(admin.views.settings))

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
    from extensions import list_extensions
    from lib import tables
    
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
    import extensions

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
