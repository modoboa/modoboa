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
    squery = request.GET.get("searchquery", None)
    if squery is not None:
        q = Q(name__contains=squery)
        q |= Q(domainalias__name__contains=squery)
        domains = domains.filter(q).distinct()
    return render_listing(request, "domains", "admin/domains.html",
                          objects=domains, squery=squery)

@login_required
@permission_required("auth.add_user")
def domains_list(request):
    doms = map(lambda dom: dom.name, request.user.get_domains())
    return ajax_simple_response(doms)

def _validate_domain(request, form, successmsg, commonctx, tplname, 
                     callback=None, tpl_form_name="form"):
    """Domain form validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        try:
            domain = form.save(request.user)
        except AdminError, e:
            error = str(e)
        # except IntegrityError:
        #     error = _("An alias with this name already exists")
        else:
            if callback is not None:
                callback(request.user, domain)
            messages.info(request, successmsg, fail_silently=True)
            return ajax_response(request, url=reverse(admin.views.domains))

    commonctx[tpl_form_name] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
def newdomain(request, tplname="admin/newdomainform.html"):
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
        form = DomainFormGeneral(request.POST)
        return _validate_domain(request, form, _("Domain created"), commonctx, 
                                tplname, callback=newdomain_cb)
    form = DomainFormGeneral()
    commonctx["form"] = form
    return _render(request, tplname, commonctx)

@login_required
@permission_required("admin.change_domain")
def editdomain(request, dom_id, tplname="admin/editdomainform.html"):
    domain = Domain.objects.get(pk=dom_id)
    if not request.user.can_access(domain):
        raise PermDeniedException

    domadmins = filter(
        lambda u: request.user.can_access(u) and not u.is_superuser, 
        domain.admins
        )
    if not request.user.is_superuser:
        domadmins = filter(lambda u: u.group == "DomainAdmins", domadmins)

    instances = dict(general=domain)
    events.raiseEvent("FillDomainInstances", request.user, domain, instances)

    commonctx = {"title" : domain.name,
                 "action_label" : _("Update"),
                 "action_classes" : "submit",
                 "action" : reverse(editdomain, args=[dom_id]),
                 "formid" : "domform",
                 "domain" : domain}
    if request.method == "POST":
        form = DomainForm(request.user, request.POST, instances=instances)
        return _validate_domain(request, form, _("Domain modified"), commonctx, tplname,
                                tpl_form_name="tabs")

    commonctx["tabs"] = DomainForm(request.user, instances=instances)
    commonctx["domadmins"] = domadmins
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
            raise PermDeniedException
        if mb and mb.domain == dom:
            raise AdminError(_("You can't delete your own domain"))
        dom.delete(keepdir=keepdir)

    msg = ungettext("Domain deleted", "Domains deleted", len(selection))
    messages.info(request, msg, fail_silently=True)
    return ajax_response(request)

def _validate_alias(request, form, successmsg, tplname, commonctx, callback=None):
    """Alias validation

    Common function shared between creation and modification actions.
    """
    error = None
    if form.is_valid():
        form.set_recipients()
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

def _new_alias(request, tplname, formclass, ctx, successmsg):
    events.raiseEvent("CanCreate", request.user, "mailbox_aliases")
    ctx.update(action_label=_("Create"), action_classes="submit")
    if request.method == "POST":
        def callback(user, alias):
            grant_access_to_object(user, alias, is_owner=True)
            events.raiseEvent("MailboxAliasCreated", user, alias)
            if user.is_superuser:
                for admin in alias.domain.admins:
                    grant_access_to_object(admin, alias)

        form = formclass(request.user, request.POST)
        return _validate_alias(request, form, successmsg, tplname, ctx, callback)

    form = formclass(request.user)
    ctx["form"] = form
    return _render(request, tplname, ctx)

@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newdlist(request):
    ctx = dict(title=_("New distribution list"), 
               action=reverse(newdlist),
               formid="aliasform")
    return _new_alias(request, "common/generic_modal_form.html", 
                      DlistForm, ctx, _("Distribution list created"))

@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newalias(request):
    ctx = dict(title=_("New alias"), 
               action=reverse(newalias),
               formid="aliasform")
    return _new_alias(request, "common/generic_modal_form.html", 
                      AliasForm, ctx, _("Alias created"))

@login_required
@permission_required("admin.add_alias")
@transaction.commit_on_success
def newforward(request):
    ctx = dict(title=_("New forward"), 
               action=reverse(newforward),
               formid="aliasform")
    return _new_alias(request, "common/generic_modal_form.html", 
                      ForwardForm, ctx, _("Forward created"))

def _edit_alias(request, alias, tplname, formclass, ctx, successmsg):
    if not request.user.can_access(alias):
        raise PermDeniedException
    ctx.update(title=alias.full_address, action_label=_("Update"),
               action_classes="submit")
    if request.method == "POST":
        form = formclass(request.user, request.POST, instance=alias)
        return _validate_alias(request, form, successmsg, tplname, ctx)

    form = formclass(request.user, instance=alias)
    ctx["form"] = form
    return _render(request, tplname, ctx)

def editalias(request, alias, ctx):
    return _edit_alias(request, alias, "common/generic_modal_form.html",
                       AliasForm, ctx, _("Alias modified"))

def editdlist(request, alias, ctx):
    return _edit_alias(request, alias, "admin/dlistform.html",
                       DlistForm, ctx, _("Distribution list modified"))

def editforward(request, alias, ctx):
    return _edit_alias(request, alias, "common/generic_modal_form.html",
                       ForwardForm, ctx, _("Forward modified"))

@login_required
@permission_required("admin.change_alias")
def editalias_dispatcher(request, alid):
    alias = Alias.objects.get(pk=alid)
    ctx = dict(action=reverse(editalias_dispatcher, args=[alias.id]), formid="aliasform")
    if len(alias.get_recipients()) >= 2:
        return editdlist(request, alias, ctx)
    if alias.extmboxes != "":
        return editforward(request, alias, ctx)
    return editalias(request, alias, ctx)

def _del_alias(request, msg, msgs):
    selection = request.GET["selection"].split(",")
    for alid in selection:
        alias = Alias.objects.get(pk=alid)
        if not request.user.can_access(alias):
            raise PermDeniedException
        alias.delete()

    msg = ungettext(msg, msgs, len(selection))
    messages.info(request, msg)
    return ajax_response(request)

@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def delalias(request):
    return _del_alias(request, "Alias deleted", "Aliases deleted")

@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def deldlist(request):
    return _del_alias(request, "Distribution list deleted", "Distribution lists deleted")

@login_required
@permission_required("admin.delete_alias")
@transaction.commit_on_success
def delforward(request):
    return _del_alias(request, "Forward deleted", "Forwards deleted")

@login_required
@user_passes_test(lambda u: u.has_perm("auth.add_user") or u.has_perm("admin.add_alias"))
def identities(request, tplname='admin/identities.html'):
    idents_list = request.user.get_identities()
    squery = request.GET.get("searchquery", None)
    if squery:
        uct = get_content_type(User)
        uids = idents_list.filter(content_type=uct).values_list("object_id", flat=True)
        objects = [u for u in User.objects.filter(pk__in=uids, username__contains=squery)]
        alct = get_content_type(Alias)
        alids = idents_list.filter(content_type=alct).values_list("object_id", flat=True)
        if squery.find('@') != -1:
            local_part, domname = split_mailbox(squery)
            mbaliases = Alias.objects.filter(address__contains=local_part,
                                             domain__name__contains=domname)
            q = Q(address__contains=local_part, domain__name__contains=domname)
        else:
            q = Q(address__contains=squery)
        objects += [al for al in Alias.objects.filter(Q(pk__in=alids) & q)]
    else:
        objects = []
        for oa in idents_list:
            if oa.content_object:
                objects.append(oa.content_object)
    objects = sorted(objects, key=lambda o: o.identity)
    return render_listing(request, "identities", tplname, 
                          objects=objects, squery=squery)

@login_required
@permission_required("auth.add_user")
def accounts_list(request):
    accs = User.objects.filter(is_superuser=False).exclude(groups__name='SimpleUsers')
    res = map(lambda a: a.username, accs.all())
    return ajax_simple_response(res)

@login_required
@permission_required("admin.add_mailbox")
def mboxes_list(request):
    mboxes = request.user.get_mailboxes()
    return ajax_simple_response([mb.full_address for mb in mboxes])

@login_required
@permission_required("auth.add_user")
@transaction.commit_on_success
def newaccount(request, tplname='admin/newaccount.html'):
    from modoboa.lib.formutils import CreationWizard

    def create_account(steps):
        """Account creation callback

        Called when all creation steps have been validated.

        :param steps: the steps data
        """
        genform = steps[0]["form"]
        genform.is_valid()
        account = genform.save()
        grant_access_to_object(request.user, account, is_owner=True)
        events.raiseEvent("AccountCreated", account)

        mailform = steps[1]["form"]
        mb = mailform.save(request.user, account)

    ctx = dict(
        title=_("New account"),
        action=reverse(newaccount),
        formid="newaccount_form",
        submit_label=_("Create")
        )
    cwizard = CreationWizard(create_account)
    cwizard.add_step(AccountFormGeneral, _("General"),
                     [dict(classes="btn-inverse next", label=_("Next"))],
                     new_args=[request.user])
    cwizard.add_step(AccountFormMail, _("Mail"),
                     [dict(classes="btn-primary submit", label=_("Create")),
                      dict(classes="btn-inverse prev", label=_("Previous"))])

    if request.method == "POST":
        retcode, data = cwizard.validate_step(request)
        if retcode == -1:
            raise AdminError(data)
        if retcode == 1:
            return ajax_simple_response(dict(
                    status="ok", title=cwizard.get_title(data + 1), stepid=data
                    ))
        if retcode == 2:
            messages.info(request, _("Account created"))
            return ajax_simple_response(dict(status="ok"))

        from modoboa.lib.templatetags.libextras import render_form
        return ajax_simple_response(dict(
                status="ko", stepid=data, form=render_form(cwizard.steps[data]["form"])
                ))

    cwizard.create_forms()
    ctx.update(steps=cwizard.steps)
    ctx.update(subtitle="1. %s" % cwizard.steps[0]['title'])
    return _render(request, tplname, ctx)

@login_required
@permission_required("auth.change_user")
@transaction.commit_on_success
def editaccount(request, accountid, tplname="common/tabforms.html"):
    account = User.objects.get(pk=accountid)
    if not request.user.can_access(account):
        raise PermDeniedException
    mb = None
    if account.has_mailbox:
        mb = account.mailbox_set.all()[0]

    instances = dict(general=account, mail=mb, perms=account)
    events.raiseEvent("FillAccountInstances", request.user, account, instances)

    ctx = dict(
        title=account.username,
        formid="accountform",
        action=reverse(editaccount, args=[accountid]),
        action_label=_("Update"),
        action_classes="submit"
        )

    if request.method == "POST":
        classes = {}
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
@permission_required("auth.delete_user")
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
@permission_required("admin.add_domain")
def remove_permission(request):
    domid = request.GET.get("domid", None)
    daid = request.GET.get("daid", None)
    if domid is None or daid is None:
        raise AdminError(_("Invalid request"))
    try:
        account = User.objects.get(pk=daid)
        domain = Domain.objects.get(pk=domid)
    except (User.DoesNotExist, Domain.DoesNotExist):
        raise AdminError(_("Invalid request"))
    if not request.user.can_access(account) or not request.user.can_access(domain):
        raise PermDeniedException
    ungrant_access_to_object(domain, account)
    return ajax_simple_response(dict(status="ok"))

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
            "selection" : "settings",
            "left_selection" : "parameters",
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
    from modoboa.extensions import exts_pool
        
    exts = exts_pool.list_all()
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
            "selection" : "settings",
            "left_selection" : "extensions",
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
    """Specific code for domains import"""
    dom = Domain()
    dom.create_from_csv(user, row)
    grant_access_to_object(user, dom, is_owner=True)
    events.raiseEvent("CreateDomain", user, dom)

def import_account(user, row):
    """Specific code for accounts import"""
    mb = Mailbox()
    mb.create_from_csv(user, row)
    grant_access_to_object(user, mb.user, is_owner=True)
    grant_access_to_object(user, mb, is_owner=True)
    events.raiseEvent("AccountCreated", mb.user)
    events.raiseEvent("CreateMailbox", user, mb)

def import_dlist(user, row):
    """Specific code for distribution lists import"""
    dlist = Alias()
    dlist.create_from_csv(user, row)
    grant_access_to_object(user, dlist, is_owner=True)
    events.raiseEvent("MailboxAliasCreated", user, dlist)

def importdata(request):
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
            try:
                cpt = 0
                for row in reader:
                    try:
                        fct = globals()["import_%s" % row[0].strip()]
                    except KeyError:
                        continue
                    fct(request.user, row)
                    cpt += 1
                messages.info(request, _("%d objects imported successfully" % cpt))
                return _render(request, "admin/import_done.html", {
                        "status" : "ok", "msg" : ""
                        })
            except (IntegrityError, ModoboaException), e:
                error = str(e)
                print error

    return _render(request, "admin/import_done.html", {
            "status" : "ko", "msg" : error
            })

@login_required
@user_passes_test(lambda u: u.has_perm("auth.add_user") or u.has_perm("auth.add_alias"))
@transaction.commit_on_success
def import_identities(request):
    if request.method == "POST":
        return importdata(request)

    helptext = _("""Provide a CSV file where lines respect one of the following format:
<ul>
<li><em>account; loginname; password; first name; last name; address</em></li>
<li><em>dlist; address; recipient; recipient; ...</em></li>
</ul>
You can use a different character as separator.
""")
    ctx = dict(
        title=_("Import identities"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse(import_identities),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportDataForm(),
        helptext=helptext
        )
    return _render(request, "admin/importform.html", ctx)

@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
def import_domains(request):
    if request.method == "POST":
        return importdata(request)

    helptext = _("""Provide a CSV file where lines respect the following format:<br/>
<em>domain; name; quota</em><br/>

You can use a different character as separator.
""")

    ctx = dict(
        title=_("Import domains"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse(import_domains),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        helptext=helptext,
        form=ImportDataForm()
        )
    return _render(request, "admin/importform.html", ctx)
