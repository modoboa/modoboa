"""Core dashboard views."""

from dateutil import parser
import feedparser

from django.views import generic

from django.contrib.auth import mixins as auth_mixins

from .. import signals


class DashboardView(auth_mixins.AccessMixin, generic.TemplateView):
    """Dashboard view."""

    template_name = "core/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        """Check if user can access dashboard."""
        if not request.user.is_authenticated or not request.user.is_admin:
            return self.handle_no_permission()
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add context variables."""
        context = super(DashboardView, self).get_context_data(**kwargs)
        context.update({
            "selection": "dashboard", "widgets": {"left": [], "right": []}
        })
        # Fetch latest news
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
        context["widgets"]["left"].append("core/_latest_news_widget.html")
        context.update({"news": entries})
        # Extra widgets
        result = signals.extra_admin_dashboard_widgets.send(
            sender=self.__class__, user=self.request.user)
        for receiver, widgets in result:
            for widget in widgets:
                context["widgets"][widget["column"]].append(
                    widget["template"])
                # FIXME: can raise conflicts...
                context.update(widget["context"])
        return context
