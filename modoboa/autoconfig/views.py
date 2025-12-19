import copy
import plistlib
import uuid

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from modoboa.lib.email_utils import split_address


def gen_subst_conn_settings(emailaddress: str, local_part: str, domain: str):
    conn_settings = copy.deepcopy(settings.EMAIL_CLIENT_CONNECTION_SETTINGS)
    for proto, proto_settings in conn_settings.items():
        for name, value in proto_settings.items():
            if isinstance(value, str):
                value = value.replace("%EMAILADDRESS%", emailaddress)
                value = value.replace("%EMAILLOCALPART%", local_part)
                value = value.replace("%EMAILDOMAIN%", domain)
                # %REALNAME% is skipped since it useless and hard cross-protocol
                proto_settings[name] = value
    return conn_settings


class ConfigBaseMixin:

    content_type = "application/xml"

    def get_common_context(self, emailaddress: str) -> dict:
        local_part, domain = split_address(emailaddress)
        return {
            "emailaddress": emailaddress,
            "domain": domain,
            "connection_settings": gen_subst_conn_settings(emailaddress, local_part, domain),
        }


class AutoConfigView(ConfigBaseMixin, generic.TemplateView):

    # Format documentation:
    # https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat

    http_method_names = ["get"]
    template_name = "autoconfig/autoconfig.xml"

    def get_context_data(self, **kwargs):
        emailaddress = self.request.GET.get("emailaddress")
        if not emailaddress:
            raise Http404
        context = super().get_context_data(**kwargs)
        # Technically Thunderbird clients could also do placeholder
        # substitution client-side, but for cross-platform consistency we
        # always do it server-side
        #
        # (Plus what are the odds that there ISN’T a broken client out there
        # that would mess this up?)
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


class MobileConfigView(generic.View):

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        emailaddress = self.request.GET.get("emailaddress")
        if not emailaddress:
            raise Http404
        local_part, domain = split_address(emailaddress)
        conn_settings = gen_subst_conn_settings(emailaddress, local_part, domain)
        parts = domain.split(".")
        parts.reverse()
        reverse_domain = ".".join(parts)
        profile = {
            "PayloadType": "Configuration",
            "PayloadVersion": 1,
            "PayloadIdentifier": f"{reverse_domain}.mailprofile",
            "PayloadUUID": str(uuid.uuid4()),
            "PayloadDisplayName": f"{domain} Mail Configuration",
            "PayloadOrganization": domain,
            "PayloadContent": [
                {
                    "PayloadType": "com.apple.mail.managed",
                    "PayloadVersion": 1,
                    "PayloadIdentifier": f"{reverse_domain}.mailprofile.mail",
                    "PayloadUUID": str(uuid.uuid4()),
                    "PayloadDisplayName": "Mail",
                    "EmailAccountDescription": f"{domain} Mail",
                    "EmailAccountType": "EmailTypeIMAP",
                    "EmailAddress": emailaddress,
                    # incoming
                    "IncomingMailServerHostName": conn_settings["imap"]["HOSTNAME"],
                    "IncomingMailServerPortNumber": conn_settings["imap"]["PORT"],
                    "IncomingMailServerUseSSL": True,
                    "IncomingMailServerUsername": emailaddress,
                    # outgoing
                    "OutgoingMailServerHostName": conn_settings["smtp"]["HOSTNAME"],
                    "OutgoingMailServerPortNumber": conn_settings["smtp"]["PORT"],
                    "IncomingMailServerUseSSL": True,
                    "OutgoingMailServerUsername": emailaddress,
                    "OutgoingPasswordSameAsIncomingPassword": True,
                }
            ],
        }
        plist_bytes = plistlib.dumps(profile, fmt=plistlib.FMT_XML)
        resp = HttpResponse(
            plist_bytes, content_type="application/x-apple-aspen-config"
        )
        resp["Content-Disposition"] = 'attachment; filename="mail.mobileconfig"'
        return resp
