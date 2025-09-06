"""
A management command to load Modoboa initial data.

* Create a default super admin if none exists
* Create groups and permissions

"""

from functools import reduce
import os
import shutil
import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from oauth2_provider.models import get_application_model

from modoboa.lib.permissions import add_permissions_to_group
from ... import constants, extensions, models, signals


class Command(BaseCommand):
    """Command definition."""

    help = "Load Modoboa initial data"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--name", help="The name of your Modoboa instance", default="instance"
        )
        parser.add_argument(
            "--admin-username",
            default="admin",
            help="Username of the initial super administrator.",
        )
        (
            parser.add_argument(
                "--extra-fixtures",
                action="store_true",
                default=False,
                help="Also load some fixtures from the admin application.",
            ),
        )
        parser.add_argument(
            "--dev",
            action="store_true",
            default=False,
            help="Setup dev environment. DO NOT USE IN PRODUCTION",
        )
        parser.add_argument(
            "--no-frontend",
            action="store_true",
            default=False,
            help="Omit everything related to frontend initialisation",
        )
        parser.add_argument(
            "--relative-urls-in-config",
            action="store_true",
            default=False,
            help="Use relative urls in generated config.json file",
        )

    def handle(self, *args, **options):
        """Command entry point."""
        extensions.exts_pool.load_all()

        if not models.User.objects.filter(is_superuser=True).count():
            admin = models.User(username=options["admin_username"], is_superuser=True)
            admin.set_password("password")
            admin.save()
            models.ObjectAccess.objects.create(
                user=admin, content_object=admin, is_owner=True
            )

        groups = list(constants.PERMISSIONS.keys())
        for groupname in groups:
            group, created = Group.objects.get_or_create(name=groupname)
            results = signals.extra_role_permissions.send(
                sender=self.__class__, role=groupname
            )
            permissions = constants.PERMISSIONS.get(groupname, [])
            if results:
                permissions += reduce(
                    lambda a, b: a + b, [result[1] for result in results]
                )
            if not permissions:
                continue
            add_permissions_to_group(group, permissions)

        for extname in list(extensions.exts_pool.extensions.keys()):
            extension = extensions.exts_pool.get_extension(extname)
            try:
                extension.load_initial_data()
            except Exception as e:
                self.stderr.write(
                    f"Unable to load initial data for '{extname}' ({str(e)})."
                )
            else:
                signals.initial_data_loaded.send(sender=self.__class__, extname=extname)

        if options["extra_fixtures"]:
            from modoboa.admin import factories

            factories.populate_database()

        if options["no_frontend"]:
            return

        app_model = get_application_model()
        allowed_host = getattr(settings, "ALLOWED_HOSTS", None)
        if allowed_host is None:
            allowed_host = input("What will be the hostname used to access Modoboa? ")
            if not allowed_host:
                allowed_host = "localhost"
            allowed_host = [allowed_host]
        frontend_application = app_model.objects.filter(name="modoboa_frontend")
        # TODO : improve support for multiple allowed_host for frontend
        base_uris_list = [f"https://{host}" for host in allowed_host]
        base_uris = " ".join(base_uris_list)
        base_uri = base_uris_list[0]
        redirect_uris = " ".join([f"{uri}/login/logged" for uri in base_uris_list])
        if not options["relative_urls_in_config"]:
            redirect_uri = redirect_uris.split(" ")[0]
        else:
            redirect_uri = "/login/logged"
        client_id = ""
        if options["dev"]:
            base_uri = "https://localhost:3000/"
            base_uris = base_uri
            redirect_uri = "https://localhost:3000/login/logged"
            redirect_uris = redirect_uri
            client_id = "LVQbfIIX3khWR3nDvix1u9yEGHZUxcx53bhJ7FlD"
        if not frontend_application.exists():
            if not options["dev"]:
                client_id = str(uuid.uuid4())
            call_command(
                "createapplication",
                "--algorithm=RS256",
                f"--redirect-uris={redirect_uris}",
                "--name=modoboa_frontend",
                f"--client-id={client_id}",
                f"--post-logout-redirect-uris={base_uris}",
                "--skip-authorization",
                "public",
                "authorization-code",
            )
        else:
            app = frontend_application.first()
            app.redirect_uris = redirect_uris
            app.post_logout_redirect_uris = base_uris
            app.save()
            client_id = app.client_id

        base_frontend_dir = os.path.join(
            os.path.dirname(__file__), "../../../frontend_dist/"
        )
        frontend_target_dir = f"{settings.BASE_DIR}/frontend"
        if os.path.isdir(base_frontend_dir):
            shutil.rmtree(frontend_target_dir, ignore_errors=True)
            os.makedirs(frontend_target_dir, exist_ok=True)
            for entry in os.scandir(base_frontend_dir):
                if entry.name != "config.json":
                    os.symlink(
                        f"{base_frontend_dir}/{entry.name}",
                        f"{frontend_target_dir}/{entry.name}",
                        target_is_directory=entry.is_dir(),
                    )
            api_base_url = "/api/v2"
            api_doc_url = "/api/schema-v2/swagger/"
            oauth_authority_url = "/api/o"
            if not options["relative_urls_in_config"]:
                api_base_url = f"{base_uri}{api_base_url}"
                api_doc_url = f"{base_uri}{base_uri}"
                oauth_authority_url = f"{base_uri}{oauth_authority_url}"
                oauth_post_logout_redirect_uri = base_uri
            else:
                oauth_post_logout_redirect_uri = ""

            with open(f"{frontend_target_dir}/config.json", "w") as fp:
                fp.write(
                    f"""{{
  "API_BASE_URL": "{api_base_url}",
  "API_DOC_URL": "{api_doc_url}",
  "OAUTH_AUTHORITY_URL": "{oauth_authority_url}",
  "OAUTH_CLIENT_ID": "{client_id}",
  "OAUTH_REDIRECT_URI": "{redirect_uri}",
  "OAUTH_POST_REDIRECT_URI": "{oauth_post_logout_redirect_uri}"
}}
"""
                )


# ADD SIGNAL FOR THAT
# def load_initial_data(self):
#     """Create records for existing domains and co."""
#     for dom in Domain.objects.all():
#         policy = create_user_and_policy("@{0}".format(dom.name))
#         for domalias in dom.domainalias_set.all():
#             domalias_pattern = "@{0}".format(domalias.name)
#             create_user_and_use_policy(domalias_pattern, policy)
