"""Core API v2 views."""

from functools import reduce
import logging

from dateutil import parser
import feedparser

from django.conf import settings

from django.core.files.storage import default_storage

from drf_spectacular.utils import extend_schema
from rest_framework import parsers, permissions, response
from rest_framework.views import APIView

from modoboa.admin import models as admin_models
from modoboa.core import models, signals
from modoboa.core.extensions import exts_pool
from modoboa.core.utils import check_for_updates, get_capabilities
from modoboa.lib.permissions import IsSuperUser, IsPrivilegedUser
from modoboa.lib.throttle import UserLesserDdosUser

from . import serializers

logger = logging.getLogger("modoboa.auth")

MODOBOA_WEBSITE_URL = "https://modoboa.org/"


class ComponentsInformationAPIView(APIView):
    """Retrieve information about installed components."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.ModoboaComponentSerializer(many=True))
    def get(self, request, *args, **kwargs):
        status, extensions = check_for_updates()
        serializer = serializers.ModoboaComponentSerializer(extensions, many=True)
        return response.Response(serializer.data)


class NotificationsAPIView(APIView):
    """Return list of active notifications."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.NotificationSerializer(many=True))
    def get(self, request, *args, **kwargs):
        notifications = signals.get_top_notifications.send(
            sender="top_notifications", include_all=False
        )
        notifications = reduce(
            lambda a, b: a + b, [notif[1] for notif in notifications]
        )
        serializer = serializers.NotificationSerializer(notifications, many=True)
        return response.Response(serializer.data)


class CapabilitiesAPIView(APIView):
    """Return the capability of this Modoboa instance."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserLesserDdosUser]

    def get(self, *args, **kwargs):
        return response.Response({"capabilities": get_capabilities()})


class ThemeAPIView(APIView):
    """Return the theme values of this Modoboa instance."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.ThemeSerializer)
    def get(self, request, *args, **kwargs):
        values = {}
        params = [
            "theme_primary_color",
            "theme_primary_color_dark",
            "theme_primary_color_light",
            "theme_secondary_color",
            "theme_label_color",
            "theme_login_logo_url",
            "theme_menu_logo_url",
            "theme_creation_form_logo_url",
        ]
        for param in params:
            values[param] = request.localconfig.parameters.get_value(param)
        results = signals.get_theme_parameters.send(
            sender=self.__class__, current_values=values
        )
        for _receiver, result in results:
            if result:
                values.update(result)
        return response.Response(values)


class ThemeLogoUploadAPIView(APIView):
    """Upload or clear a custom theme logo."""

    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    parser_classes = [parsers.MultiPartParser]

    @extend_schema(
        request=serializers.ThemeLogoUploadSerializer,
        responses=serializers.ThemeLogoUploadSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.ThemeLogoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logo_type = serializer.validated_data["logo_type"]
        image = serializer.validated_data["image"]

        stored_path = default_storage.save(
            f"theme_logos/{logo_type}_{image.name}", image
        )
        url = default_storage.url(stored_path)

        param_name = f"theme_{logo_type}_logo_url"
        request.localconfig.parameters.set_value(param_name, url, app="core")
        request.localconfig.save()

        return response.Response({"logo_type": logo_type, "url": url})

    def delete(self, request, *args, **kwargs):
        logo_type = request.query_params.get("logo_type")
        if logo_type not in serializers.ThemeLogoUploadSerializer.LOGO_TYPES:
            return response.Response(
                {"logo_type": "Invalid or missing logo_type."},
                status=400,
            )

        param_name = f"theme_{logo_type}_logo_url"
        request.localconfig.parameters.set_value(param_name, "", app="core")
        request.localconfig.save()

        return response.Response(status=204)


class NewsFeedAPIView(APIView):
    """Return list of latest news from configured RSS feed."""

    permission_classes = [permissions.IsAuthenticated, IsPrivilegedUser]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.NewsFeedEntrySerializer(many=True))
    def get(self, request, *args, **kwargs):
        lang = "fr" if request.user.language == "fr" else "en"
        feed_url = f"{MODOBOA_WEBSITE_URL}{lang}/weblog/feeds/"
        show_rss_feed_to_superadmins = request.localconfig.parameters.get_value(
            "show_rss_feed_to_superadmins"
        )
        if request.user.role != "SuperAdmins" or show_rss_feed_to_superadmins:
            custom_feed_url = request.localconfig.parameters.get_value("rss_feed_url")
            if custom_feed_url:
                feed_url = custom_feed_url
        entries = []
        if not settings.DISABLE_DASHBOARD_EXTERNAL_QUERIES:
            posts = feedparser.parse(feed_url)
            for entry in posts["entries"][:5]:
                entry["published"] = parser.parse(entry["published"])
                entries.append(entry)

        serializer = serializers.NewsFeedEntrySerializer(entries, many=True)
        return response.Response(serializer.data)


class FrontendPluginsAPIView(APIView):
    """Expose registered Modoboa plugins frontend manifest."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.FrontendPluginManifestSerializer(many=True))
    def get(self, request, *args, **kwargs):
        manifests = exts_pool.get_frontend_manifests()
        serializer = serializers.FrontendPluginManifestSerializer(manifests, many=True)
        return response.Response(serializer.data)


class StatisticsAPIView(APIView):
    """Return some statistics about this modoboa instance."""

    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    throttle_classes = [UserLesserDdosUser]

    @extend_schema(responses=serializers.StatisticsSerializer())
    def get(self, request, *args, **kwargs):
        data = {
            "domain_count": admin_models.Domain.objects.count(),
            "domain_alias_count": admin_models.DomainAlias.objects.count(),
            "account_count": models.User.objects.count(),
            "alias_count": admin_models.Alias.objects.filter(internal=False).count(),
        }
        serializer = serializers.StatisticsSerializer(data)
        return response.Response(serializer.data)
