from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.core import serializers
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from mailng import admin
from mailng.admin.models import Domain, Mailbox, Alias
from forms import MailboxForm, DomainForm, AliasForm

def _ctx_ok(url):
    return {"status" : "ok", "url" : url}

def _ctx_ko(tpl, ctx):
    return {"status" : "ko", "content" : render_to_string(tpl, ctx)}

def _render(request, tpl, user_context):
    return render_to_response(tpl, user_context, 
                              context_instance=RequestContext(request))

@login_required
def domains(request):
    domains = Domain.objects.all()
    counters = {}
    for dom in domains:
        dom.mboxcounter = len(dom.mailbox_set.all())
    return _render(request, 'admin/domains.html', {
            "domains" : domains, "counters" : counters
            })

@login_required
def newdomain(request):
    if request.method == "POST":
        form = DomainForm(request.POST)
        error = None
        if form.is_valid():
            if Domain.objects.filter(name=request.POST["name"]):
                error = "Domain with this name already defined"
            else:
                form.save()
                ctx = _ctx_ok(reverse(admin.views.domains))
                return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
        ctx = _ctx_ko("admin/newdomain.html", {
                "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm()
    return render_to_response('admin/newdomain.html', {
            "form" : form
            })
@login_required   
def editdomain(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
    if request.method == "POST":
        form = DomainForm(request.POST, instance=domain)
        if form.is_valid():
            form.save()
            ctx = _ctx_ok(reverse(admin.views.domains))
            return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
        ctx = _ctx_ko("admin/editdomain.html", {
                "domain" : domain, "form" : form
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = DomainForm(instance=domain) 
    return render_to_response('admin/editdomain.html', {
            "domain" : domain, "form" : form
            })

@login_required
def deldomain(request, dom_id):
    domain = Domain.objects.get(pk=dom_id)
    domain.delete()
    return HttpResponseRedirect('/mailng/admin/')

@login_required
def mailboxes(request, dom_id=None):
    domain = Domain.objects.get(pk=dom_id)
    mailboxes = Mailbox.objects.filter(domain=dom_id)
    return _render(request, 'admin/mailboxes.html', {
            "mailboxes" : mailboxes, "domain" : domain
            })

@login_required
def newmailbox(request, dom_id=None):
    domain = Domain.objects.get(pk=dom_id)
    if request.method == "POST":
        form = MailboxForm(request.POST)
        error = None
        if form.is_valid():
            if Mailbox.objects.filter(address=request.POST["address"],
                                      domain=dom_id):
                error = "Mailbox with this address already exists"
            else:
                mb = form.save(commit=False)
                user = User()
                user.username = user.email = "%s@%s" % (mb.address, domain.name)
                user.set_password(request.POST["password1"])
                user.is_active = request.POST.has_key("enabled") \
                    and True or False
                fname, lname = mb.name.split()
                user.first_name = fname

                user.last_name = lname
                user.save()
                mb.user = user

                mb.uid = mb.gid = 500
                mb.domain = domain
                mb.save()
                ctx = _ctx_ok(reverse(admin.views.mailboxes, args=[domain.id]))
                return HttpResponse(simplejson.dumps(ctx), 
                                    mimetype="application/json")
        ctx = _ctx_ko("admin/newmailbox.html", {
                "form" : form, "domain" : domain, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = MailboxForm()
    return render_to_response('admin/newmailbox.html', {
            "domain" : domain, "form" : form
            })

@login_required
def editmailbox(request, dom_id, mbox_id=None):
    mb = Mailbox.objects.get(pk=mbox_id)
    if request.method == "POST":
        form = MailboxForm(request.POST, instance=mb)
        if form.is_valid():
            if request.POST["enabled"] != mb.user.is_active \
                    or request.POST["password1"] != mb.user.password:
                mb.user.is_active = request.POST["enabled"]
                mb.user.password = request.POST["password1"]
                mb.user.save()
            form.save()
            ctx = _ctx_ok(reverse(admin.views.mailboxes, args=[dom_id]))
        else:
            ctx = _ctx_ko("admin/editmailbox.html", {
                    "mbox" : mb, "form" : form
                    })
        json = simplejson.dumps(ctx)
        return HttpResponse(json, mimetype="application/json")

    form = MailboxForm(instance=mb)
    form.fields['enabled'].initial = mb.user.is_active
    form.fields['password1'].initial = mb.user.password
    form.fields['password2'].initial = mb.user.password
    return _render(request, 'admin/editmailbox.html', {
            "form" : form, "mbox" : mb
            })

@login_required
def delmailbox(request, dom_id, mbox_id=None):
    mb = Mailbox.objects.get(pk=mbox_id)
    mb.delete()
    return HttpResponseRedirect(reverse(admin.views.mailboxes, 
                                        args=[dom_id]))

@login_required
def aliases(request, dom_id=None, mbox_id=None):
    domain = Domain.objects.get(pk=dom_id)
    if not mbox_id:
        mboxes = Mailbox.objects.filter(domain=dom_id)
        aliases = []
        for mb in mboxes:
            aliases += Alias.objects.filter(mbox=mb.id)
    else:
        aliases = Alias.objects.filter(mbox=mbox_id)
    return _render(request, 'admin/aliases.html', {
            "aliases" : aliases, "domain" : domain
            })

@login_required
def newalias(request, dom_id, mbox_id):
    mbox = Mailbox.objects.get(pk=mbox_id)
    if request.method == "POST":
        form = AliasForm(request.POST)
        if form.is_valid():
            form.save()
            ctx = _ctx_ok(reverse(admin.views.aliases, args=[mbox.domain.id]))
        else:
            ctx = _ctx_ko("admin/newalias.html", {
                    "mbox" : mbox, "form" : form
                    })
        json = simplejson.dumps(ctx)
        return HttpResponse(json, mimetype="application/json")

    form = AliasForm({"mbox" : mbox_id}, domain=mbox.domain)
    return render_to_response('admin/newalias.html', {
            "mbox" : mbox, "form" : form, "noerrors" : True
            })

@login_required
def editalias(request, dom_id, alias_id):
    alias = Alias.objects.get(pk=alias_id)
    if request.method == "POST":
        form = AliasForm(request.POST, instance=alias)
        if form.is_valid():
            form.save()
            ctx = _ctx_ok(reverse(admin.views.aliases, args=[dom_id]))
        else:
            ctx = _ctx_ko("admin/editalias.html", {
                    "alias" : alias, "form" : form
                    })
        json = simplejson.dumps(ctx)
        return HttpResponse(json, mimetype="application/json")
    form = AliasForm(instance=alias)
    return _render(request, 'admin/editalias.html', {
            "form" : form, "alias" : alias
            })

@login_required
def delalias(request, dom_id, alias_id):
    alias = Alias.objects.get(pk=alias_id)
    alias.delete()
    return HttpResponseRedirect(reverse(admin.views.aliases, 
                                        args=[dom_id]))

