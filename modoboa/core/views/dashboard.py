"""Core dashboard views."""

from dateutil import parser
import feedparser

from django.views import generic

from django.contrib.auth import mixins as auth_mixins


class DashboardView(auth_mixins.AccessMixin, generic.TemplateView):
    """Dashboard view."""

    template_name = "core/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        """Check if user can access dashboard."""
        if not request.user.is_admin:
            return self.handle_no_permission()
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add context variables."""
        context = super(DashboardView, self).get_context_data(**kwargs)
        context.update({"selection": "dashboard"})
        if self.request.user.language == "fr":
            lang = "fr"
        else:
            lang = "en"
        posts = feedparser.parse(
            "https://modoboa.org/{}/weblog/feeds/".format(lang))
        entries = []
        for entry in posts["entries"][:5]:
            entry["published"] = parser.parse(entry["published"])
            entries.append(entry)
        context.update({"news": entries})
        return context
