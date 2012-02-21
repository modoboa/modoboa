# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import transaction, IntegrityError, transaction

from lib import *
from modoboa import admin, userprefs
from models import *
from modoboa.admin.permissions import *
from modoboa.admin.tables import *
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import *
from modoboa.lib.webutils \
    import _render, ajax_response, ajax_simple_response, getctx
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.models import Parameter
import copy

@login_required
def domains(request):
    if not request.user.has_perm("admin.view_domains"):
        if request.user.has_perm("admin.view_mailboxes"):
            return HttpResponseRedirect(reverse(mailboxes))

        return HttpResponseRedirect(reverse(userprefs.views.preferences))
    
    domains = request.user.get_domains()
    for dom in domains:
        dom.mbalias_counter = len(Alias.objects.filter(domain=dom.id))
    deloptions = {"keepdir" : _("Do not delete domain directory")}
    return render_listing(request, "domains",
                          "admin/domains.html",
                          title=_("Available domains"),
                          objects=domains,
                          rel="310 190",
                          deloptions=deloptions)

def _validate_domain(request, form, successmsg, commonctx, 
                     callback=None, tplname="admin/adminform.html"):
    """Domain validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        try:
            domain = form.save()
        except AdminError, e:
            error = str(e)
        except IntegrityError:
            error = _("Domain with this name already defined")
        else:
            if callback is not None:
                callback(request.user, domain)
            messages.info(request, successmsg, fail_silently=True)
            return ajax_response(request, url=reverse(admin.views.domains))

    commonctx["form"] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
def newdomain(request, tplname="admin/adminform.html"):
    events.raiseEvent("CanCreate", request.user, "domains")
    def newdomain_cb(user, domain):
        grant_access_to_object(user, domain, is_owner=True)
        events.raiseEvent("CreateDomain", user, domain)

    commonctx = {"title" : _("New domain"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newdomain),
                 "formid" : "domform"}
    if request.method == "POST":
        form = DomainForm(request.POST)
        return _validate_domain(request, form, _("Domain created"), commonctx, 
                                newdomain_cb)
                                
    form = DomainForm()
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id, tplname="admin/adminform.html"):
    domain = Domain.objects.get(pk=dom_id)
    if not request.user.is_owner(domain):
        raise PermDeniedException(_("You can't edit this domain"))

    commonctx = {"title" : _("Domain editing"),
                 "submit_label" : _("Update"),
                 "action" : reverse(editdomain, args=[dom_id]),
                 "formid" : "domform"}
    if request.method == "POST":
        form = DomainForm(request.POST, instance=domain)
        return _validate_domain(request, form, _("Domain modified"), commonctx)

    form = DomainForm(instance=domain)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.delete_domain")
@transaction.commit_on_success
def deldomain(request):
    selection = request.GET["selection"].split(",")
    error = None
    keepdir = True if request.GET.get("keepdir", "false") == "true" else False
    try:
        mb = Mailbox.objects.get(user__id=request.user.id)
    except Mailbox.DoesNotExist:
        mb = None

    for dom in Domain.objects.filter(id__in=selection):
        if not request.user.is_owner(dom):
            raise PermDeniedException(_("You can't delete this domain"))
        if mb and mb.domain == dom:
            raise AdminError(_("You can't delete your own domain"))

        events.raiseEvent("DeleteDomain", dom)
        ungrant_access_to_object(dom)
        dom.delete(keepdir=keepdir)

    msg = ungettext("Domain deleted", "Domains deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@permission_required("admin.view_domaliases")
@check_domain_access
def domaliases(request):
    if request.GET.has_key("domid"):
        domain = Domain.objects.get(pk=request.GET["domid"])
        domaliases = DomainAlias.objects.filter(target=request.GET["domid"])
    else:
        domain = None
        domaliases = request.user.get_domaliases()
    return render_listing(request, "domaliases",
                               title=_("Domain aliases"),
                               rel="310 190",
                               objects=domaliases)

@login_required
@permission_required("admin.add_domainalias")
@transaction.commit_on_success
def newdomalias(request, tplname="admin/adminform.html"):
    events.raiseEvent("CanCreate", request.user, "domain_aliases")
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
                    grant_access_to_object(request.user, domalias, is_owner=True)
                    events.raiseEvent("DomainAliasCreated", request.user, domalias)
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
@permission_required("admin.change_domainalias")
def editdomalias(request, alias_id, tplname="admin/adminform.html"):
    domalias = DomainAlias.objects.get(pk=alias_id)
    if not request.user.is_owner(domalias.target):
        raise PermDeniedException(_("You do not have access to this domain"))

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
@permission_required("admin.delete_domainalias")
@transaction.commit_on_success
def deldomalias(request):
    selection = request.GET["selection"].split(",")
    for daid in selection:
        domalias = DomainAlias.objects.get(pk=daid)
        if not request.user.is_owner(domalias.target):
            raise PermDeniedException(_("You don't have acces to this domain"))
        events.raiseEvent("DomainAliasDeleted", domalias)
        ungrant_access_to_object(domalias)
        domalias.delete()
    msg = ungettext("Domain alias deleted", "Domain aliases deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@permission_required("admin.view_mailboxes")
@check_domain_access
def mailboxes(request):
    title = _("Available mailboxes")
    if request.GET.has_key("domid"):
        domain = Domain.objects.get(pk=request.GET["domid"])
        mboxes = Mailbox.objects.filter(domain=domain.id)
        title += " (%s)" % domain.name
    else:
        mboxes = request.user.get_mailboxes()
        domain = None
    deloptions = {"keepdir" : _("Do not delete mailbox directory")}
    return render_listing(request, "mailboxes",
                          title=title,
                          rel="310 320",
                          objects=mboxes, domain=domain, deloptions=deloptions)

@login_required
@permission_required("admin.view_mailboxes")
@check_domain_access
def mailboxes_search(request):
    if request.method != "POST":
        return
    local_part, domain = split_mailbox(request.POST["search"])
    query = Q(address__startswith=local_part)
    if domain is not None and domain != "":
        query &= Q(domain__name__startswith=domain)
    if request.GET.has_key("domid"):
        query = Q(domain=request.GET["domid"]) & query
    elif not request.user.is_superuser:
        query = Q(domain__in=request.user.get_domains()) & query
    mboxes = Mailbox.objects.filter(query)
    result = map(lambda mb: mb.full_address, mboxes)
    return ajax_simple_response(result)

@login_required
@permission_required("admin.add_mailbox")
@transaction.commit_on_success
def newmailbox(request, tplname="admin/adminform.html"):
    events.raiseEvent("CanCreate", request.user, "mailboxes")
    commonctx = {"title" : _("New mailbox"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newmailbox),
                 "formid" : "mboxform"}
    if request.method == "POST":
        form = MailboxWithPasswordForm(request.user, request.POST)
        error = None
        if form.is_valid():
            if not request.user.is_superuser:
                if not request.user.can_access(form.cleaned_data["domain"]):
                    raise PermDeniedException(_("You do not have access to this domain"))

            try:
                mb = form.save()
            except AdminError as e:
                error = str(e)
            else:
                grant_access_to_object(request.user, mb, is_owner=True)
                grant_access_to_object(request.user, mb.user, is_owner=True)
                events.raiseEvent("CreateMailbox", request.user, mb)
                messages.info(request, _("Mailbox created"),
                              fail_silently=True)
                return ajax_response(request, url=reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = MailboxWithPasswordForm(request.user)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.change_mailbox")
def editmailbox(request, mbox_id=None, tplname="admin/adminform.html"):
    mb = Mailbox.objects.get(pk=mbox_id)
    if not request.user.can_access(mb.domain):
        raise PermDeniedException(_("You do not have access to this domain"))

    commonctx = {"title" : _("Mailbox editing"),
                 "submit_label" : _("Create"),
                 "action" : reverse(editmailbox, args=[mbox_id]),
                 "formid" : "mboxform"}
    if request.method == "POST":
        if request.POST.get("password1", "") != "" or \
           request.POST.get("password2", "") != "":
            formclass = MailboxWithPasswordForm
        else:
            formclass = MailboxForm
        oldmb = copy.deepcopy(mb)
        form = formclass(request.user, request.POST, instance=mb)
        error = None
        if form.is_valid():
            try:
                mb = form.save(commit=False)
            except AdminError, inst:
                error = str(inst)
            else:
                if oldmb.rename_dir(mb.domain.name, mb.address):
                    form.commit_save(mb)
                    events.raiseEvent("ModifyMailbox", mb, oldmb)
                    messages.info(request, _("Mailbox modified"),
                                  fail_silently=True)
                    return ajax_response(request, url=reverse(admin.views.mailboxes) + "?domid=%d" % mb.domain.id)
                error = _("Failed to rename mailbox, check permissions")                

        commonctx["form"] = form
        commonctx["error"] = error
        return ajax_response(request, status="ko", template=tplname, **commonctx)

    form = MailboxWithPasswordForm(request.user, instance=mb)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.delete_mailbox")
@transaction.commit_on_success
def delmailbox(request):
    selection = request.GET["selection"].split(",")
    error = None
    keepdir = True if request.GET.get("keepdir", "false") == "true" else False
    usermb = request.user.mailbox_set.all()[0] \
        if len(request.user.mailbox_set.all()) else None

    for mb in Mailbox.objects.filter(id__in=selection):
        if not request.user.can_access(mb.domain):
            raise PermDeniedException(_("You don't have access to this domain"))
        if usermb and usermb == mb:
            raise AdminError(_("You can't delete your own mailbox"))
        events.raiseEvent("DeleteMailbox", mb)
        ungrant_access_to_object(mb)
        ungrant_access_to_object(mb.user)
        mb.delete(keepdir=keepdir)

    msg = ungettext("Mailbox deleted", "Mailboxes deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

@login_required
@permission_required("admin.view_aliases")
@check_domain_access
def mbaliases(request):
    if request.GET.has_key("domid"):
        aliases = Alias.objects.filter(domain=request.GET["domid"])
    elif request.GET.has_key("mbid"):
        aliases = Alias.objects.filter(mboxes__id=request.GET["mbid"]).distinct()
    else:
        aliases = request.user.get_mbaliases()
    
    return render_listing(request, "mbaliases",
                          title=_("Mailbox aliases"),
                          rel="320 300",
                          objects=aliases)

def _validate_mbalias(request, form, successmsg, tplname, commonctx, callback=None):
    """Mailbox alias validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        if not request.POST.has_key("targets"):
            raise AdminError(_("No target defined"))
        form.set_targets(request.user, request.POST.getlist("targets"))
        try:
            alias = form.save()
        except IntegrityError:
            raise AdminError(_("Alias with this name already exists"))
            
        if callback:
            callback(request.user, alias)

        messages.info(request, successmsg, fail_silently=True)
        return ajax_response(request, url=reverse(admin.views.mbaliases))

    if request.POST.has_key("targets"):
        targets = request.POST.getlist("targets")
        commonctx["targets"] = targets[:-1]

    commonctx["form"] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newmbalias(request, tplname="admin/mbaliasform.html"):
    events.raiseEvent("CanCreate", request.user, "mailbox_aliases")
    commonctx = {"title" : _("New mailbox alias"),
                 "submit_label" : _("Create"),
                 "action" : reverse(newmbalias),
                 "formid" : "mbaliasform"}
    if request.method == "POST":
        def callback(user, mbalias):
            grant_access_to_object(user, mbalias, is_owner=True)
            events.raiseEvent("MailboxAliasCreated", user, mbalias)

        form = AliasForm(request.user, request.POST)
        return _validate_mbalias(request, form, _("Mailbox alias created"),
                                 tplname, commonctx, callback)

    form = AliasForm(request.user)
    commonctx["form"] = form
    commonctx["noerrors"] = True
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.change_alias")
def editmbalias(request, alias_id, tplname="admin/mbaliasform.html"):
    alias = Alias.objects.get(pk=alias_id)
    if not request.user.is_owner(alias.domain):
        raise PermDeniedException(_("You do not have access to this domain"))
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
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def delmbalias(request):
    selection = request.GET["selection"].split(",")
    for mbaid in selection:
        mbalias = Alias.objects.get(pk=mbaid)
        if not request.user.is_owner(mbalias.domain):
            raise PermDeniedException(_("You do not have access to this domain"))
        events.raiseEvent("MailboxAliasDeleted", mbalias)
        ungrant_access_to_object(mbalias)
        mbalias.delete()

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

    permtables += events.raiseQueryEvent("PermsGetTables", request)

    permtables += [
        {"id" : "domain_admins",
         "title" : _("Domain administrators"),
         "rel" : "350 100",
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
        events.raiseEvent("CanCreate", request.user, role)
        pobj = pclass()
        if request.method == "GET":
            return pobj.get_add_form(request)
        status, data = pobj.add(request)
        if not status:
            return HttpResponse(simplejson.dumps(data), mimetype="application/json")
        try:
            msg = pobj.add_success_msg
        except AttributeError:
            msg = _("Permission added")
        messages.info(request, msg, fail_silently=True)
    return ajax_response(request, url=reverse(admin.views.permissions))

@login_required
@permission_required("auth.view_permissions")
def create_domain_admin(request, tplname="admin/create_domain_admin.html"):
    events.raiseEvent("CanCreate", request.user, "domain_admins")
    if request.method == "POST":
        form = UserWithPasswordForm(request.POST)
        if form.is_valid():
            user = form.save(group="DomainAdmins")
            grant_access_to_object(request.user, user, is_owner=True)
            events.raiseEvent("DomainAdminCreated", user)
            messages.info(request, _("Domain admin created"), fail_silently=True)
            return ajax_response(request, url=reverse(admin.views.permissions))

        return ajax_response(request, status="ko", template=tplname, form=form)

    form = UserWithPasswordForm()
    return ajax_response(request, template=tplname, form=form)

@login_required
@permission_required("auth.view_permissions")
def edit_domain_admin(request, da_id, tplname="admin/adminform.html"):
    ctx = dict(title=_("Edit domain admin"), 
               action=reverse(edit_domain_admin, args=[da_id]),
               formid="eda_form",
               submit_label=_("Update"))
    u = User.objects.get(pk=da_id, groups__name="DomainAdmins")
    if request.method == "POST":
        if request.POST.get("password1", "") != "" and \
                request.POST.get("password2", "") != "":
            form = UserWithPasswordForm(request.POST, instance=u)
        else:
            form = UserForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            if form.cleaned_data["createmb"]:
                pass
            messages.info(request, _("Domain admin updated"), fail_silently=True)
            return ajax_response(request, 
                                 url=reverse("modoboa.admin.views.permissions"))
        ctx.update(form=form)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = UserWithPasswordForm(instance=u)
    ctx.update(form=form)
    return _render(request, tplname, ctx)

@login_required
@permission_required("auth.view_permissions")
def domain_admin_promotion(request, tplname="admin/domain_admin_promotion.html"):
    if request.method == "POST":
        form = DomainAdminPromotionForm(request.POST)
        if form.is_valid():
            u = User.objects.get(username=form.cleaned_data["name"])
            u.groups.add(Group.objects.get(name="DomainAdmins"))
            u.save()
            if not request.user.can_access(u):
                # The only case where we need to grant access to the
                # object is when ``u`` has been create by a super
                # admin
                grant_access_to_object(request.user, u, is_owner=True)
            events.raiseEvent("DomainAdminCreated", u)
            messages.info(request, _("Domain admin added"), fail_silently=True)
            return ajax_response(request, url=reverse(admin.views.permissions))

        return ajax_response(request, status="ko", template=tplname, form=form)

    form = DomainAdminPromotionForm()
    return ajax_response(request, template=tplname, form=form)

@login_required
@permission_required("auth.view_permissions")
@transaction.commit_on_success
def assign_domains_to_admin(request, da_id, tplname="admin/adminform.html"):
    da = User.objects.get(pk=da_id)
    ctx = dict(title=_("Assign domains to %s" % da.username),
               action=reverse(assign_domains_to_admin, args=[da_id]),
               formid="assignform",
               submit_label=_("Assign"))
    if request.method == "POST":
        form = AssignDomainsForm(request.user, da, request.POST)
        if form.is_valid():
            current_domains = da.get_domains()
            for domain in form.cleaned_data["domains"]:
                if not domain in current_domains:
                    grant_access_to_object(da, domain)
                else:
                    current_domains.remove(domain)
            for domain in current_domains:
                ungrant_access_to_object(domain, da)
            msg = ungettext("Domain assigned", "Domains assigned", 
                            len(form.cleaned_data["domains"]))
            messages.info(request, msg)
            return ajax_response(request, url=reverse(admin.views.permissions))
        ctx.update(form=form)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = AssignDomainsForm(request.user, da)
    ctx.update(form=form)
    return _render(request, tplname, ctx)

@login_required
@permission_required("auth.view_permissions")
def view_domain_admins(request, dom_id, tplname="admin/view_domain_admins.html"):
    domain = Domain.objects.get(pk=dom_id)
    return _render(request, tplname, {
            "domain" : domain
            })

@login_required
@permission_required("auth.view_permissions")
@check_domain_access
def search_account(request):
    search = request.POST.get("search", None)
    if search is None:
        return ajax_simple_response([])

    query = Q(username__startswith=search)
    query &= Q(is_superuser=False)
    if not request.user.has_perm("admin.add_domain"):
        query &= Q(groups__name="SimpleUsers")
    else:
        query &= ~Q(groups__name__in=["DomainAdmins"])

    users = User.objects.filter(query)
    result = map(lambda u: u.username, users.all())
    return ajax_simple_response(result)

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
            
    tbl = ExtensionsTable(request, exts)
    return _render(request, tplname, {
            "extensions" : tbl
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
            else:
                found += [dbext]
    for ext in actived_exts:
        if not ext in found:
            ext.off()
    messages.info(request, _("Modifications applied."), fail_silently=True)
    return HttpResponseRedirect(reverse(admin.views.viewextensions))

@login_required
@permission_required("admin.add_mailbox")
@transaction.commit_on_success
def importdata(request, tplname="admin/import.html"):
    if request.method == "POST":
        error = None
        form = ImportDataForm(request.POST, request.FILES)
        if form.is_valid():
            import csv
            reader = csv.reader(request.FILES['sourcefile'], 
                                delimiter=form.cleaned_data['sepcar'])
            try:
                cpt = 0
                for row in reader:
                    mb = Mailbox()
                    mb.create_from_csv(request.user, row)
                    events.raiseEvent("CreateMailbox", request.user, mb)
                    cpt += 1
                messages.info(request, _("%d mailboxes imported successfully" % cpt))
                return _render(request, "admin/import_done.html", {
                        "status" : "ok", "msg" : ""
                        })
            except ModoboaException, e:
                error = str(e)

        return _render(request, "admin/import_done.html", {
                "status" : "ko", "msg" : error
                })

    form = ImportDataForm()
    ctx = dict(title=_("Import data"), action="", formid="importform", 
               enctype="multipart/form-data", form=form, submit_label=_("Import"))
    return _render(request, tplname, ctx)

