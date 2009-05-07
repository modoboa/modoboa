from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.decorators \
    import login_required
from mailng.lib import _render
from forms import ARmessageForm

@login_required
def index(request):
    return _render(request, "main/index.html", {})

@login_required
def autoreply(request):
    form = ARmessageForm()
    return _render(request, "main/autoreply.html", {
            "form" : form
            })
