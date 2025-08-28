from django.core.management.base import BaseCommand, CommandError

from oauth2_provider.models import get_application_model


class Command(BaseCommand):
    """Command class."""

    help = "Add new allowed hosts to frontend Oauth2 application."

    def add_arguments(self, parser):
        parser.add_argument("hostnames", type=str, nargs="+")

    def handle(self, *args, **options):
        app_model = get_application_model()
        app = app_model.objects.filter(name="modoboa_frontend").first()
        if not app:
            raise CommandError(
                "Application modoboa_frontend not found. "
                "Make sure you ran load_initial_data first."
            )
        redirect_uris = app.redirect_uris.split(" ")
        post_logout_redirect_uris = app.post_logout_redirect_uris.split(" ")
        for hostname in options["hostnames"]:
            uri = f"https://{hostname}/login/logged"
            if uri not in redirect_uris:
                redirect_uris.append(uri)
            uri = f"https://{hostname}"
            if uri not in post_logout_redirect_uris:
                post_logout_redirect_uris.append(uri)
        app.redirect_uris = " ".join(redirect_uris)
        app.post_logout_redirect_uris = " ".join(post_logout_redirect_uris)
        app.save()
