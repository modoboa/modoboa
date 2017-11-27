"""Transport views."""

from django import http
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views import generic

from django.contrib.auth import mixins as auth_mixins
from django.contrib import messages

from . import backends
from . import forms
from . import models


class TransportListView(
        auth_mixins.PermissionRequiredMixin, generic.ListView):
    """ListView for Transport."""

    model = models.Transport
    permission_required = "transport.add_transport"
    template_name = "transport/transport_list.html"

    def get_context_data(self, **kwargs):
        """Inject search query."""
        context = super(TransportListView, self).get_context_data(**kwargs)
        context.update({
            "selection": "domains",
            "squery": self.request.GET.get("searchquery")
        })
        return context

    def get_queryset(self):
        """Filter."""
        qs = super(TransportListView, self).get_queryset()
        searchquery = self.request.GET.get("searchquery")
        if searchquery:
            qs = qs.filter(pattern__icontains=searchquery)
        return qs


class TransportMixin(object):
    """Mixin for Transport creation/update."""

    form_class = forms.TransportForm
    model = models.Transport
    success_message = ugettext_lazy("Transport created")
    success_url = reverse_lazy("transport:transport_list")
    template_name = "transport/_transport_form.html"

    def form_invalid(self, form):
        """Return JSON response."""
        return http.JsonResponse({
            "form_errors": form.errors,
            "prefix": form.prefix
        }, status=400)

    def form_valid(self, form):
        """Save transport."""
        transport = form.save(commit=False)
        backend = backends.manager.get_backend(transport.service)
        backend.serialize(transport)
        options = {}
        if not transport.pk:
            options.update({"creator": self.request.user})
        transport.save(**options)
        messages.success(self.request, self.success_message)
        return http.JsonResponse({})

    def get_context_data(self, **kwargs):
        """Include extra data."""
        context = super(TransportMixin, self).get_context_data(
            **kwargs)
        setting_fields = []
        for fname in context["form"].setting_fields:
            setting_fields.append(context["form"][fname])
        context.update({
            "action_classes": "submit",
            "formid": "transport_form",
            "setting_fields": setting_fields
        })
        return context


class TransportCreateView(
        auth_mixins.PermissionRequiredMixin,
        TransportMixin,
        generic.CreateView):
    """Transport create view."""

    permission_required = "transport.add_transport"

    def get_context_data(self, **kwargs):
        """Include extra data."""
        context = super(TransportCreateView, self).get_context_data(
            **kwargs)
        context.update({
            "action": reverse("transport:transport_create"),
            "action_label": _("Create"),
            "title": _("New transport"),
        })
        return context


class TransportUpdateView(
        auth_mixins.PermissionRequiredMixin,
        TransportMixin,
        generic.UpdateView):
    """Transport update view."""

    permission_required = "transport.change_transport"
    success_message = ugettext_lazy("Transport updated")

    def get_context_data(self, **kwargs):
        """Include extra data."""
        context = super(TransportUpdateView, self).get_context_data(
            **kwargs)
        context.update({
            "action": reverse(
                "transport:transport_update", args=[self.object.pk]),
            "action_label": _("Update"),
            "title": _("Edit transport"),
        })
        return context


class TransportDeleteView(
        auth_mixins.PermissionRequiredMixin,
        TransportMixin,
        generic.DeleteView):
    """Transport delete view."""

    model = models.Transport
    permission_required = "transport.del_transport"
    success_url = reverse_lazy("transport:transport_list")

    def delete(self, request, *args, **kwargs):
        """Add message."""
        response = super(TransportDeleteView, self).delete(
            request, *args, **kwargs)
        messages.success(request, _("Transport deleted"))
        return response
