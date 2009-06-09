from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.decorators \
    import login_required
from mailng.lib import _render
from forms import ARmessageForm
from models import ARmessage
from admin.models import Mailbox

@login_required
def index(request):
    return _render(request, "main/index.html", {})

@login_required
def autoreply(request):
    mb = Mailbox.objects.get(user=request.user.id)
    try:
        arm = ARmessage.objects.get(mbox=mb.id)
    except ARmessage.DoesNotExist:
        arm = None
    if request.method == "POST":
        if arm:
            form = ARmessageForm(request.POST, instance=arm)
        else:
            form = ARmessageForm(request.POST)
        error = None
        if form.is_valid():
            arm = form.save(commit=False)
            arm.mbox = mb
            arm.save()
            
    form = ARmessageForm(instance=arm)
    return _render(request, "main/autoreply.html", {
            "form" : form
            })

