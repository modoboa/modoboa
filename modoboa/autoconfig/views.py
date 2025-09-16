import uuid

from django.conf import settings
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from modoboa.lib.email_utils import split_address


class ConfigBaseMixin:

    content_type = "application/xml"

    def get_common_context(self, emailaddress: str) -> dict:
        local_part, domain = split_address(emailaddress)
        return {
            "emailaddress": emailaddress,
            "domain": domain,
            "connection_settings": settings.EMAIL_CLIENT_CONNECTION_SETTINGS,
        }


class AutoConfigView(ConfigBaseMixin, generic.TemplateView):

    http_method_names = ["get"]
    template_name = "autoconfig/autoconfig.xml"

    def get_context_data(self, **kwargs):
        emailaddress = self.request.GET.get("emailaddress")
        if not emailaddress:
            raise Http404
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context(emailaddress))
        return context


@method_decorator(csrf_exempt, name="dispatch")
class AutoDiscoverView(ConfigBaseMixin, generic.TemplateView):

    http_method_names = ["post"]
    template_name = "autoconfig/autodiscover.xml"

    def get_context_data(self, **kwargs):
        emailaddress = self.request.POST.get("EmailAddress")
        if not emailaddress:
            raise Http404
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context(emailaddress))
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class MobileConfigView(ConfigBaseMixin, generic.TemplateView):

    content_type = "application/x-apple-aspen-config"
    http_method_names = ["get"]
    template_name = "autoconfig/mobileconfig.xml"

    def get_context_data(self, **kwargs):
        emailaddress = self.request.GET.get("email")
        if not emailaddress:
            raise Http404
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context(emailaddress))
        parts = context["domain"].split(".")
        parts.reverse()
        context.update(
            {
                "reverse_domain": ".".join(parts),
                "content_uuid": uuid.uuid4(),
                "global_uuid": uuid.uuid4(),
            }
        )
        return context

    def render_to_response(self, context, **responsse_kwargs):
        content = render_to_string(self.template_name, context)
        response = HttpResponse(content, content_type=self.content_type)
        response["Content-Disposition"] = 'attachment; filename="mail.mobileconfig"'
        return response
