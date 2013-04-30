# coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, permission_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render
from django.db import transaction, IntegrityError
import cStringIO
import csv

from lib import *
from forms import *
from models import * 
from modoboa.admin.tables import *
from modoboa.lib import events, parameters
from modoboa.lib.exceptions import *
from modoboa.lib.webutils \
    import _render, ajax_response, ajax_simple_response, _render_to_string
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.models import Parameter
from modoboa.lib.formutils import CreationWizard


@login_required
def index(request):
    return HttpResponseRedirect(reverse(domains))

@login_required
@user_passes_test(lambda u: u.has_perm("admin.view_domains") or u.has_perm("admin.view_mailboxes"))
def _domains(request):
    domains = request.user.get_domains()
    squery = request.GET.get("searchquery", None)
    if squery is not None:
        q = Q(name__contains=squery)
        q |= Q(domainalias__name__contains=squery)
        domains = domains.filter(q).distinct()
    return render_listing(request, "domains", objects=domains)

@login_required
def domains(request, tplname="admin/domains.html"):
    if not request.user.has_perm("admin.view_domains"):
        if request.user.has_perm("admin.view_mailboxes"):
            return HttpResponseRedirect(reverse(identities))
        
        return HttpResponseRedirect(reverse("modoboa.userprefs.views.index"))
    
    return render(request, tplname, {
            "selection" : "domains"
            })

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
        else:
            if callback is not None:
                callback(request.user, domain)
            return ajax_simple_response({"status" : "ok", "respmsg" : successmsg})

    commonctx[tpl_form_name] = form
    commonctx["error"] = error
    return ajax_response(request, status="ko", template=tplname, **commonctx)

@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
def newdomain(request, tplname="common/wizard_forms.html"):
    events.raiseEvent("CanCreate", request.user, "domains")
   
    def newdomain_cb(steps):
        genform = steps[0]["form"]
        genform.is_valid()
        domain = genform.save(request.user)
        domain.post_create(request.user)
        steps[1]["form"].save(request.user, domain)

    commonctx = {"title" : _("New domain"),
                 "action_label" : _("Create"),
                 "action_classes" : "submit",
                 "action" : reverse(newdomain),
                 "formid" : "domform"}
    cwizard = CreationWizard(newdomain_cb)
    cwizard.add_step(DomainFormGeneral, _("General"),
                     [dict(classes="btn-inverse next", label=_("Next"))],
                     formtpl="admin/domain_general_form.html")
    cwizard.add_step(DomainFormOptions, _("Options"),
                     [dict(classes="btn-primary submit", label=_("Create")),
                      dict(classes="btn-inverse prev", label=_("Previous"))],
                     formtpl="admin/domain_options_form.html")

    if request.method == "POST":
        retcode, data = cwizard.validate_step(request)
        if retcode == -1:
            raise AdminError(data)
        if retcode == 1:
            return ajax_simple_response(dict(
                status="ok", title=cwizard.get_title(data + 1), stepid=data
            ))
        if retcode == 2:
            return ajax_simple_response(dict(status="ok", respmsg=_("Domain created")))

        from modoboa.lib.templatetags.libextras import render_form
        return ajax_simple_response(dict(
            status="ko", stepid=data, form=render_form(cwizard.steps[data]["form"])
        ))

    cwizard.create_forms()
    commonctx.update(steps=cwizard.steps)
    commonctx.update(subtitle="1. %s" % cwizard.steps[0]['title'])
    return render(request, tplname, commonctx)

@login_required
@permission_required("admin.view_domains")
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
        def editdomain_cb(user, newdomain):
            events.raiseEvent("DomainModified", domain)

        domain.oldname = domain.name
        form = DomainForm(request.user, request.POST, instances=instances)
        return _validate_domain(request, form, _("Domain modified"), commonctx, tplname,
                                tpl_form_name="tabs", callback=editdomain_cb)

    commonctx["tabs"] = DomainForm(request.user, instances=instances)
    commonctx["domadmins"] = domadmins
    return render(request, tplname, commonctx)

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
        dom.delete(request.user, keepdir)

    msg = ungettext("Domain deleted", "Domains deleted", len(selection))
    return ajax_simple_response({"status" : "ok", "respmsg" : msg})

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
        return ajax_simple_response({"status" : "ok", "respmsg" : successmsg})

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
            alias.post_create(user)

        form = formclass(request.user, request.POST)
        return _validate_alias(request, form, successmsg, tplname, ctx, callback)

    form = formclass(request.user)
    ctx["form"] = form
    return render(request, tplname, ctx)

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
    return render(request, tplname, ctx)

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
    return ajax_simple_response({"status" : "ok", "respmsg" : msg})

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
def _identities(request):
    idents_list = request.user.get_identities(request.GET)
    objects = sorted(idents_list, key=lambda o: o.identity)
    
    paginator = Paginator(objects, int(parameters.get_admin("ITEMS_PER_PAGE")))
    pagenum = int(request.GET.get("page", "1"))
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(paginator.num_pages)
    
    return ajax_simple_response({
        "table" : _render_to_string(request, "admin/identities_table.html", {
            "identities" : page.object_list,
            "tableid" : "objects_table"
        }),
        "handle_mailboxes": parameters.get_admin("HANDLE_MAILBOXES", raise_error=False),
        "page" : page.number,
        "paginbar" : pagination_bar(page)
    })

@login_required
@user_passes_test(lambda u: u.has_perm("auth.add_user") or u.has_perm("admin.add_alias"))
def identities(request, tplname="admin/identities.html"):
    return render(request, tplname, {
            "selection" : "identities",
            "deflocation" : "list/"
            })

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
@permission_required("admin.add_mailbox")
def list_quotas(request, tplname="admin/quotas.html"):
    sort_order = request.GET.get("sort_order", "address")
    mboxes = request.user.get_mailboxes(request.GET.get("searchquery", None))
    mboxes = mboxes.exclude(quota=0)
    if sort_order.startswith("-"):
        sort_dir = "-"
        sort_order = sort_order[1:]
    else:
        sort_dir = ""
    if sort_order in ["address", "quota", "quota_value__bytes"]:
        mboxes = mboxes.order_by("%s%s" % (sort_dir, sort_order))
    elif sort_order == "quota_usage":
        mboxes = mboxes.extra(
            select={'quota_usage': 'admin_quota.bytes / (admin_mailbox.quota * 1048576) * 100'},
            where=["admin_quota.mbox_id=admin_mailbox.id"],
            tables=["admin_quota"],
            order_by=["%s%s" % (sort_dir, sort_order)]
        )
    else:
        raise AdminError(_("Invalid request"))
    paginator = Paginator(mboxes, int(parameters.get_admin("ITEMS_PER_PAGE")))
    pagenum = int(request.GET.get("page", "1"))
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(paginator.num_pages)
    return ajax_simple_response({
        "status": "ok",
        "page": page.number,
        "paginbar": pagination_bar(page),
        "table": _render_to_string(request, tplname, {
            "mboxes": page
        })
    })


@login_required
@permission_required("auth.add_user")
@transaction.commit_on_success
def newaccount(request, tplname='common/wizard_forms.html'):
    def create_account(steps):
        """Account creation callback

        Called when all creation steps have been validated.

        :param steps: the steps data
        """
        genform = steps[0]["form"]
        genform.is_valid()
        account = genform.save()
        account.post_create(request.user)

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
                      dict(classes="btn-inverse prev", label=_("Previous"))],
                     formtpl="admin/mailform.html")

    if request.method == "POST":
        retcode, data = cwizard.validate_step(request)
        if retcode == -1:
            raise AdminError(data)
        if retcode == 1:
            return ajax_simple_response(dict(
                    status="ok", title=cwizard.get_title(data + 1), stepid=data
                    ))
        if retcode == 2:
            return ajax_simple_response(dict(status="ok", respmsg=_("Account created")))

        from modoboa.lib.templatetags.libextras import render_form
        return ajax_simple_response(dict(
                status="ko", stepid=data, form=render_form(cwizard.steps[data]["form"])
                ))

    cwizard.create_forms()
    ctx.update(steps=cwizard.steps)
    ctx.update(subtitle="1. %s" % cwizard.steps[0]['title'])
    return render(request, tplname, ctx)

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
                return ajax_simple_response(dict(status="ok", respmsg=_("Account updated")))
            transaction.rollback()

        ctx["tabs"] = form
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["tabs"] = AccountForm(request.user, instances=instances)
    active_tab_id = request.GET.get("active_tab", "default")
    if active_tab_id != "default":
        ctx["tabs"].active_id = active_tab_id
    return render(request, tplname, ctx)

@login_required
@permission_required("auth.delete_user")
@transaction.commit_on_success
def delaccount(request):
    selection = request.GET["selection"].split(",")
    keepdir = True if request.GET.get("keepdir", "false") == "true" else False

    for account in User.objects.filter(id__in=selection):
        account.delete(request.user, keepdir)

    msg = ungettext("Account deleted", "Accounts deleted", len(selection))
    return ajax_simple_response({"status" : "ok", "respmsg" : msg})

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
    domain.remove_admin(account)
    return ajax_simple_response(dict(status="ok"))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewsettings(request, tplname='admin/settings_header.html'):
    return render(request, tplname, {
            "selection" : "settings"
            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewparameters(request, tplname='admin/parameters.html'):
    return ajax_simple_response({
        "status" : "ok",
        "left_selection" : "parameters",
        "content" : render_to_string(tplname, {"forms" : parameters.get_admin_forms})
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveparameters(request):
    for formdef in parameters.get_admin_forms(request.POST):
        form = formdef["form"]
        if form.is_valid():
            form.save()
            form.to_django_settings()
            continue
        return ajax_simple_response({"status": "ko", "prefix": form.app, "errors": form.errors})
    return ajax_simple_response(dict(status="ok", respmsg=_("Parameters saved")))

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
    return ajax_simple_response({
            "status" : "ok",
            "content" : render_to_string(tplname, {"extensions" : tbl})
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
            status="ok", respmsg=_("Modifications applied.")
            ))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def information(request, tplname="admin/information.html"):
    return ajax_simple_response({
            "status" : "ok", 
            "content" : render_to_string(tplname, {})
            })

@transaction.commit_on_success
def import_domain(user, row, formopts):
    """Specific code for domains import"""
    dom = Domain()
    dom.from_csv(user, row)

@transaction.commit_on_success
def import_domainalias(user, row, formopts):
    """Specific code for domain aliases import"""
    domalias = DomainAlias()
    domalias.from_csv(user, row)

@transaction.commit_on_success
def import_account(user, row, formopts):
    """Specific code for accounts import"""
    account = User()
    account.from_csv(user, row, formopts["crypt_password"])

@transaction.commit_on_success
def _import_alias(user, row, **kwargs):
    """Specific code for aliases import"""
    alias = Alias()
    alias.from_csv(user, row, **kwargs)

def import_alias(user, row, formopts):
    _import_alias(user, row, expected_elements=4)

def import_forward(user, row, formopts):
    _import_alias(user, row, expected_elements=4)

def import_dlist(user, row, formopts):
    _import_alias(user, row)

def importdata(request, formclass=ImportDataForm):
    """Generic import function

    As the process of importing data from a CSV file is the same
    whatever the type, we do a maximum of the work here.

    :param request: a ``Request`` instance
    :param typ: a string indicating the object type being imported
    :return: a ``Response`` instance
    """
    error = None
    form = formclass(request.POST, request.FILES)
    if form.is_valid():
        try:
            reader = csv.reader(request.FILES['sourcefile'], 
                                delimiter=form.cleaned_data['sepchar'])
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
                    try:
                        fct(request.user, row, form.cleaned_data)
                    except IntegrityError, e:
                        if form.cleaned_data["continue_if_exists"]:
                            continue
                        raise ModoboaException(_("Object already exists: %s" % row))
                    cpt += 1
                msg = _("%d objects imported successfully" % cpt)
                return render(request, "admin/import_done.html", {
                        "status" : "ok", "msg" : msg
                        })
            except (ModoboaException), e:
                error = str(e)

    return render(request, "admin/import_done.html", {
            "status" : "ko", "msg" : error
            })

@login_required
@user_passes_test(lambda u: u.has_perm("auth.add_user") or u.has_perm("auth.add_alias"))
def import_identities(request):
    if request.method == "POST":
        return importdata(request, ImportIdentitiesForm)

    helptext = _("""Provide a CSV file where lines respect one of the following formats:
<ul>
<li><em>account; loginname; password; first name; last name; enabled, group; address[, domain, ...]</em></li>
<li><em>alias; address; enabled; internal recipient</em></li>
<li><em>forward; address; enabled; external recipient</em></li>
<li><em>dlist; address; enabled; recipient; recipient; ...</em></li>
</ul>
<p>The first element of each line is mandatory and must be equal to one of the previous values.</p>

<p>You can use a different character as separator.</p>
""")
    ctx = dict(
        title=_("Import identities"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse(import_identities),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportIdentitiesForm(),
        helptext=helptext
        )
    return render(request, "admin/importform.html", ctx)

def _export(content, filename):
    """Export a csv file's content

    :param content: the content to export (string)
    :param filename: the name that will appear into the response
    :return: an ``HttpResponse`` object
    """
    resp = HttpResponse(content)
    resp["Content-Type"] = "text/csv"
    resp["Content-Length"] = len(content)
    resp["Content-Disposition"] = 'attachment; filename="%s"' % filename
    return resp

@login_required
@permission_required(lambda u: u.has_perm("auth.add_user") or u.has_perm("auth.add_alias"))
def export_identities(request):
    ctx = {
        "title" : _("Export identities"),
        "action_label" : _("Export"),
        "action_classes" : "submit",
        "formid" : "exportform",
        "action" : reverse(export_identities),
        }

    if request.method == "POST":
        form = ExportIdentitiesForm(request.POST)
        form.is_valid()
        fp = cStringIO.StringIO()
        csvwriter = csv.writer(fp, delimiter=form.cleaned_data["sepchar"])
        for ident in request.user.get_identities():
            ident.to_csv(csvwriter)
        content = fp.getvalue()
        fp.close()
        return _export(content, form.cleaned_data["filename"])

    ctx["form"] = ExportIdentitiesForm()    
    return render(request, "common/generic_modal_form.html", ctx)

@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
def import_domains(request):
    if request.method == "POST":
        return importdata(request)

    helptext = _("""Provide a CSV file where lines respect one of the following formats:
<ul>
  <li><em>domain; name; quota; enabled</em></li>
  <li><em>domainalias; name; targeted domain; enabled</em></li>
</ul>
<p>The first element of each line is mandatory and must be equal to one of the previous values.</p>
<p>You can use a different character as separator.</p>
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
    return render(request, "admin/importform.html", ctx)

@login_required
@permission_required("admin.add_domain")
def export_domains(request):
    ctx = {
        "title" : _("Export domains"),
        "action_label" : _("Export"),
        "action_classes" : "submit",
        "formid" : "exportform",
        "action" : reverse(export_domains),
        }

    if request.method == "POST":
        form = ExportDomainsForm(request.POST)
        form.is_valid()
        fp = cStringIO.StringIO()
        csvwriter = csv.writer(fp, delimiter=form.cleaned_data["sepchar"])
        for dom in request.user.get_domains():
            dom.to_csv(csvwriter)
            for da in dom.domainalias_set.all():
                da.to_csv(csvwriter)
        content = fp.getvalue()
        fp.close()
        return _export(content, form.cleaned_data["filename"])

    ctx["form"] = ExportDomainsForm()
    return render(request, "common/generic_modal_form.html", ctx)
