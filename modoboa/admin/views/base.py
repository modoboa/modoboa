"""Admin views."""

from __future__ import unicode_literals

from django.views import generic


class AdminIndexView(generic.TemplateView):
    """Admin index view."""

    template_name = "admin/index.html"
