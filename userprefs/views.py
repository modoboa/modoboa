from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators \
    import login_required
from django.utils import simplejson
from django.utils.translation import ugettext as _
from mailng.lib import _render, _ctx_ok, _ctx_ko
from mailng.lib.authbackends import crypt_password
from forms import ChangePasswordForm
from mailng.admin.models import Mailbox

@login_required
def index(request):
    mb = Mailbox.objects.get(user=request.user.id)
    return _render(request, "userprefs/index.html", {})
    # try:
    #     arm = ARmessage.objects.filter(mbox=mb.id, enabled=True)
    # except ARmessage.DoesNotExist:
    #     arm = None
    # return _render(request, "userprefs/index.html", {"arm" : arm})


@login_required
def changepassword(request):
    mb = Mailbox.objects.get(user=request.user.id)
    error = None
    if request.method == "POST":
        form = ChangePasswordForm(mb, request.POST)
        if form.is_valid():
            mb.password = crypt_password(request.POST["confirmation"])
            mb.save()
            ctx = _ctx_ok("")
            return HttpResponse(simplejson.dumps(ctx), 
                                mimetype="application/json")
        ctx = _ctx_ko("userprefs/chpassword.html", {
                "form" : form, "error" : error
                })
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

    form = ChangePasswordForm(mb)
    return render_to_response('userprefs/chpassword.html', {
            "form" : form
            })

@login_required
def confirm(request):
    return render_to_response('userprefs/confirm.html', {
            "msg" : request.GET["question"]
            })

