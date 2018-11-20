"""App related views."""

from django.utils.translation import ugettext as _
from django.views import generic

from django.contrib.auth import mixins as auth_mixins

from modoboa.admin import models as admin_models

from . import models


class DomainAccessRequiredMixin(auth_mixins.AccessMixin):
    """Check if user can access domain."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_access(self.get_object()):
            return self.handle_no_permission()
        return super(DomainAccessRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class DNSRecordDetailView(
        auth_mixins.LoginRequiredMixin,
        DomainAccessRequiredMixin,
        generic.DetailView):
    """View to display MX records."""

    model = models.DNSRecord
    template_name = "dnstools/dns_record_detail.html"

    def get_context_data(self, **kwargs):
        """Add extra variables."""
        context = super(DNSRecordDetailView, self).get_context_data(**kwargs)
        context.update({
            "title": _("{} record of {}").format(
                self.object.type.upper(), self.object.domain)
        })
        return context


class AutoConfigRecordsStatusView(
        auth_mixins.LoginRequiredMixin,
        auth_mixins.PermissionRequiredMixin,
        generic.DetailView):
    """Autoconfig records status view."""

    model = admin_models.Domain
    permission_required = "admin.view_domain"
    template_name = "dnstools/autoconfig_records_status.html"

    def get_queryset(self):
        """Add some prefetching."""
        return (
            admin_models.Domain.objects.get_for_admin(self.request.user)
            .prefetch_related("dnsrecord_set")
        )

    def get_context_data(self, **kwargs):
        """Add extra data to context."""
        context = super(AutoConfigRecordsStatusView, self).get_context_data(
            **kwargs)
        context.update({
            "title": _("Auto configuration records for {}").format(
                self.object.name)
        })
        return context


class DomainDNSConfigurationView(
        auth_mixins.LoginRequiredMixin,
        DomainAccessRequiredMixin,
        generic.DetailView):
    """Page to display DNS configuration for a domain."""

    model = admin_models.Domain
    template_name = "dnstools/domain_dns_configuration.html"

    def get_context_data(self, **kwargs):
        """Add extra variables."""
        context = super(DomainDNSConfigurationView, self).get_context_data(
            **kwargs)
        context.update({
            "title": _("DNS configuration for {}").format(self.object)
        })
        return context
