"""Convert stored folder names after switching the IMAP separator to '/'."""

import re

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from modoboa.admin.models import Mailbox
from modoboa.lib.dovecot import DoveadmError, get_dovecot_backend
from modoboa.parameters import tools as param_tools
from modoboa.webmail import constants
from modoboa.webmail.lib.imaputils import server_info_key

OLD_SEPARATOR = "."
NEW_SEPARATOR = "/"

# The folder is the last argument of a fileinto command, after the
# optional tagged ones (:copy, :create, :flags "\\Seen"...).
FILEINTO_RE = re.compile(r'(\bfileinto\b[^;]*?)"((?:[^"\\]|\\.)*)"(\s*;)')


def convert_name(name: str) -> str:
    # With '.' as separator, a dot always is a hierarchy level
    return name.replace(OLD_SEPARATOR, NEW_SEPARATOR)


def convert_sieve_script(script: str) -> tuple[str, list[str]]:
    """Rewrite the folder names used by the fileinto commands of a script.

    :return: the new script and the folder names that changed
    """
    changed = []

    def replace(match):
        name = match.group(2)
        if OLD_SEPARATOR in name:
            changed.append(name)
        return f'{match.group(1)}"{convert_name(name)}"{match.group(3)}'

    return FILEINTO_RE.sub(replace, script), changed


class Command(BaseCommand):
    """Management command to migrate folder names to the '/' separator."""

    help = (  # NOQA:A003
        "Convert the folder names stored in Sieve scripts and user settings "
        "once Dovecot uses '/' instead of '.' as hierarchy separator"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the changes without applying them",
        )

    def migrate_sieve_scripts(self, backend, username: str, dry_run: bool) -> None:
        for name in backend.list_sieve_scripts(username):
            script, changed = convert_sieve_script(
                backend.get_sieve_script(username, name)
            )
            if not changed:
                continue
            self.stdout.write(
                f"{username}: Sieve script '{name}': " + ", ".join(sorted(set(changed)))
            )
            if not dry_run:
                backend.put_sieve_script(username, name, script)

    def migrate_settings(self, user, dry_run: bool) -> None:
        values = {}
        for parameter in constants.SPECIAL_MAILBOX_PARAMETERS:
            value = user.parameters.get_value(parameter, app="webmail")
            if value and OLD_SEPARATOR in value:
                values[parameter] = convert_name(value)
        if not values:
            return
        self.stdout.write(
            f"{user.username}: settings: "
            + ", ".join(f"{name}={value}" for name, value in values.items())
        )
        if not dry_run:
            user.parameters.set_values(values, app="webmail")
            user.save(update_fields=["_parameters"])

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        try:
            backend = get_dovecot_backend()
        except DoveadmError as err:
            raise CommandError(str(err)) from err
        conf = dict(param_tools.get_global_parameters("webmail"))
        failures = 0
        cache_keys = []
        for mailbox in Mailbox.objects.select_related("user"):
            user = mailbox.user
            try:
                self.migrate_sieve_scripts(backend, user.username, dry_run)
            except DoveadmError as err:
                # Keep going: the command can be run again once fixed
                failures += 1
                self.stderr.write(f"{user.username}: {err}")
            self.migrate_settings(user, dry_run)
            cache_keys.append(
                server_info_key(
                    conf["imap_server"], conf["imap_port"], user.username, "namespaces"
                )
            )
        if not dry_run:
            # The webmail would keep using the old separator for an hour
            cache.delete_many(cache_keys)
        if failures:
            raise CommandError(
                f"Sieve scripts of {failures} account(s) could not be migrated"
            )
