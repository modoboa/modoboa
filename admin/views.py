# coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.db.models import Q
from django.contrib import messages
from django.db import transaction, IntegrityError

from lib import render_listing
from forms import *
from modoboa import admin, userprefs
from models import * 
from modoboa.admin.tables import *
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import *
from modoboa.lib.webutils \
    import _render, ajax_response, ajax_simple_response
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.models import Parameter
from modoboa.lib.permissions import *

@login_required
def domains(request):
    if not request.user.has_perm("admin.view_domains"):
        if request.user.has_perm("admin.view_mailboxes"):
            return HttpResponseRedirect(reverse(identities))

        return HttpResponseRedirect(reverse(userprefs.views.preferences))
    
    domains = request.user.get_domains()
    for dom in domains:
        dom.mbalias_counter = len(Alias.objects.filter(domain=dom.id))
    return render_listing(request, "domains",
                          "admin/domains.html",
                          objects=domains)

@login_required
@permission_required("admin.view_domains")
def domains_list(request):
    doms = map(lambda dom: dom.name, request.user.get_domains())
    return ajax_simple_response(doms)

def _validate_domain(request, form, successmsg, commonctx, tplname, 
                     callback=None):
    """Domain form validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        try:
            domain = form.save(request.user)
        except AdminError, e:
            error = str(e)
        except IntegrityError:
            error = _("An alias with this name already exists")
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
def newdomain(request):
    events.raiseEvent("CanCreate", request.user, "domains")
    def newdomain_cb(user, domain):
        grant_access_to_object(user, domain, is_owner=True)
        events.raiseEvent("CreateDomain", user, domain)

    commonctx = {"title" : _("New domain"),
                 "action_label" : _("Create"),
                 "action_classes" : "submit",
                 "action" : reverse(newdomain),
                 "formid" : "domform"}
    if request.method == "POST":
        form = DomainForm(request.POST)
        return _validate_domain(request, form, _("Domain created"), commonctx, 
                                "admin/domainform.html",
                                callback=newdomain_cb)
    form = DomainForm()
    commonctx["form"] = form
    return _render(request, "common/generic_modal_form.html", commonctx)

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id, tplname="admin/domainform.html"):
    domain = Domain.objects.get(pk=dom_id)
    if not request.user.is_owner(domain):
        raise PermDeniedException(_("You can't edit this domain"))

    commonctx = {"title" : _("Domain editing"),
                 "action_label" : _("Update"),
                 "action_classes" : "submit",
                 "action" : reverse(editdomain, args=[dom_id]),
                 "formid" : "domform"}
    if request.method == "POST":
        form = DomainForm(request.POST, instance=domain)
        return _validate_domain(request, form, _("Domain modified"), commonctx, tplname)

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
        if not request.user.can_access(dom):
            raise PermDeniedException(_("You can't delete this domain"))
        if mb and mb.domain == dom:
            raise AdminError(_("You can't delete your own domain"))

        events.raiseEvent("DomainAliasDeleted", dom.domainalias_set.all())
        events.raiseEvent("DeleteMailbox", dom.mailbox_set.all())
        events.raiseEvent("DeleteDomain", dom)
        ungrant_access_to_object(dom)
        dom.delete(keepdir=keepdir)

    msg = ungettext("Domain deleted", "Domains deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

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

def _validate_dlist(request, form, successmsg, tplname, commonctx, callback=None):
    """Distribution list validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        form.set_recipients(request.user)
        try:
            alias = form.save()
        except IntegrityError:
            raise AdminError(_("Alias with this name already exists"))
            
        if callback:
            callback(request.user, alias)

        messages.info(request, successmsg)
        return ajax_response(request, url=reverse(admin.views.identities))

    if request.POST.has_key("targets"):
        targets = request.POST.getlist("targets")
        commonctx["targets"] = targets[:-1]

    commonctx["form"] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newdlist(request, tplname="common/generic_modal_form.html"):
    events.raiseEvent("CanCreate", request.user, "mailbox_aliases")
    commonctx = {"title" : _("New distribution list"),
                 "action_label" : _("Create"),
                 "action_classes" : "submit",
                 "action" : reverse(newdlist),
                 "formid" : "dlistform"}

    if request.method == "POST":
        def callback(user, dlist):
            grant_access_to_object(user, dlist, is_owner=True)
            events.raiseEvent("MailboxAliasCreated", user, dlist)

        form = DlistForm(request.POST)
        return _validate_dlist(request, form, _("Distribution list created"),
                               tplname, commonctx, callback)

    form = DlistForm()
    commonctx["form"] = form
    return _render(request, "common/generic_modal_form.html", commonctx)

@login_required
@permission_required("admin.change_alias")
def editdlist(request, dlist_id, tplname="admin/dlistform.html"):
    dlist = Alias.objects.get(pk=dlist_id)
    if not request.user.is_owner(dlist.domain):
        raise PermDeniedException(_("You do not have access to this domain"))
    commonctx = {"title" : dlist.full_address,
                 "action_label" : _("Update"),
                 "action_classes" : "submit",
                 "action" : reverse(editdlist, args=[dlist.id]),
                 "formid" : "dlistform"}
    if request.method == "POST":
        form = DlistForm(request.POST, instance=dlist)
        return _validate_dlist(request, form, _("Distribution list modified"),
                               tplname, commonctx)

    form = DlistForm(instance=dlist)
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def deldlist(request):
    selection = request.GET["selection"].split(",")
    for dlist_id in selection:
        dlist = Alias.objects.get(pk=dlist_id)
        if not request.user.is_owner(dlist.domain):
            raise PermDeniedException(_("You do not have access to this domain"))
        events.raiseEvent("MailboxAliasDeleted", dlist)
        ungrant_access_to_object(dlist)
        dlist.delete()

    msg = ungettext("Distribution list deleted", 
                    "Distribution lists deleted", len(selection))
    messages.info(request, msg)
    return ajax_response(request)

@login_required
@user_passes_test(lambda u: u.has_perm("auth.add_user") or u.has_perm("admin.add_mailbox"))
def identities(request, tplname='admin/identities.html'):
    accounts_list = []
    for account in User.objects.all():
        if request.user.can_access(account) or \
                account.has_mailbox and request.user.can_access(account.mailbox_set.all()[0].domain):
            accounts_list += [account]
    for mbalias in Alias.objects.all():
        if len(mbalias.get_recipients()) > 2:
            accounts_list += [mbalias]
    return render_listing(request, "identities", tplname, objects=accounts_list)

@login_required
def accounts_list(request):
    accs = User.objects.filter(is_superuser=False).exclude(groups__name='SimpleUsers')
    res = map(lambda a: a.username, accs.all())
    return ajax_simple_response(res)

@login_required
@transaction.commit_on_success
def newaccount(request, tplname='admin/newaccount.html'):
    from modoboa.lib.formutils import CreationWizard

    def create_account(steps):
        """Account creation callback

        Called when all the creation steps have been validated.

        :param steps: the steps data
        """
        genform = steps[0]["form"]
        genform.is_valid()
        account = genform.save()
        grant_access_to_object(request.user, account, is_owner=True)
        events.raiseEvent("AccountCreated", account)

        mailform = steps[1]["form"]
        mailform.save(request.user, account)

    ctx = dict(
        title=_("New account"),
        action=reverse(newaccount),
        formid="newaccount_form",
        submit_label=_("Create")
        )
    cwizard = CreationWizard(create_account)
    cwizard.add_step(AccountFormGeneralPwd, 
                     buttons=[dict(classes="btn-inverse next", label=_("Next"))],
                     new_args=[request.user])
    cwizard.add_step(AccountFormMail,
                     buttons=[dict(classes="btn-primary submit", label=_("Create")),
                              dict(classes="btn-inverse prev", label=_("Previous"))])

    if request.method == "POST":
        retcode, data = cwizard.validate_step(request)
        if retcode == -1:
            raise AdminError(data)
        if retcode == 1:
            return ajax_simple_response(dict(status="ok"))
        if retcode == 2:
            messages.info(request, _("Account created"))
            return ajax_simple_response(dict(status="ok"))
        ctx.update(steps=cwizard.steps)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    cwizard.create_forms()
    ctx.update(steps=cwizard.steps)
    return _render(request, tplname, ctx)

@login_required
@transaction.commit_on_success
def editaccount(request, accountid, tplname="common/tabforms.html"):
    account = User.objects.get(pk=accountid)
    mb = account.mailbox_set.all()[0] if account.has_mailbox else None
    instances = dict(general=account, mail=mb, perms=account)
    events.raiseEvent("FillAccountInstances", request.user, account, instances)

    ctx = dict(
        title=account.username,
        action=reverse(editaccount, args=[accountid]),
        submit_label=_("Update")
        )

    if request.method == "POST":
        classes = {}
        if request.POST.get("password1", "") == "" \
                and request.POST.get("password2", "") == "":
            classes["general"] = AccountFormGeneral
        form = AccountForm(request.user, request.POST, 
                           instances=instances, classes=classes)
        account.oldgroup = account.group
        if form.is_valid(mandatory_only=True):
            form.save_general_form()
            if form.is_valid(optional_only=True):
                events.raiseEvent("AccountModified", account, form.account)
                form.save()
                messages.info(request, _("Account updated"))
                return ajax_simple_response(dict(status="ok"))
            transaction.rollback()

        ctx["tabs"] = form
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["tabs"] = AccountForm(request.user, instances=instances)
    return _render(request, tplname, ctx)

@login_required
@user_passes_test(lambda u: u.has_perm("auth.delete_user") or \
                            u.has_perm("admin.delete_mailbox"))
@transaction.commit_on_success
def delaccount(request):
    selection = request.GET["selection"].split(",")
    keepdir = True if request.GET.get("keepdir", "false") == "true" else False

    for account in User.objects.filter(id__in=selection):
        account.delete(request.user, keepdir)

    msg = ungettext("Account deleted", "Accounts deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

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
            "selection" : "parameters",
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
    return ajax_simple_response(dict(status="ok", message=_("Parameters saved")))

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
            "selection" : "extensions",
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

    return ajax_simple_response(dict(
            status="ok", message=_("Modifications applied."), reload=True
            ))

def import_domain(user, row):
    pass

def import_account(user, row):
    """Specific code for accounts import"""
    mb = Mailbox()
    mb.create_from_csv(user, row)
    events.raiseEvent("AccountCreated", user, mb.user)
    events.raiseEvent("CreateMailbox", user, mb)
    grant_access_to_object(user, mb.user)
    grant_access_to_object(user, mb)

def importdata(request, typ):
    """Generic import function

    As the process of importing data from a CSV file is the same
    whatever the type, we do a maximum of the work here.

    :param request: a ``Request`` instance
    :param typ: a string indicating the object type being imported
    :return: a ``Response`` instance
    """
    error = None
    form = ImportDataForm(request.POST, request.FILES)
    if form.is_valid():
        import csv

        try:
            reader = csv.reader(request.FILES['sourcefile'], 
                                delimiter=form.cleaned_data['sepcar'])
        except Exception, e:
            error = str(e)

        if error is None:
            fct = globals()["import_%s" % typ]
            try:
                cpt = 0
                for row in reader:
                    fct(request.user, row)
                    cpt += 1
                messages.info(request, _("%d %s imported successfully" % (cpt, typ)))
                return _render(request, "admin/import_done.html", {
                        "status" : "ok", "msg" : ""
                        })
            except ModoboaException, e:
                error = str(e)

    return _render(request, "admin/import_done.html", {
            "status" : "ko", "msg" : error
            })

@login_required
@transaction.commit_on_success
def import_identities(request):
    if request.method == "POST":
        return importdata(request, "account")

    ctx = dict(
        title=_("Import identities"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse(import_identities),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportDataForm()
        )
    return _render(request, "admin/importform.html", ctx)

@login_required
@transaction.commit_on_success
def import_domains(request):
    if request.method == "POST":
        return importdata(request, "domain")

    ctx = dict(
        title=_("Import domains"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse(import_domains),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportDataForm()
        )
    return _render(request, "admin/importform.html", ctx)
