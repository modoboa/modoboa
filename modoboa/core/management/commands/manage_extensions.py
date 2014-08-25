# coding: utf-8
"""
A management command to enable an extension.
"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from modoboa.core.models import Extension


class Command(BaseCommand):

    """Command definition."""

    help = "Enable or disable extensions"

    option_list = BaseCommand.option_list + (
        make_option(
            "--action", type=str, default="enable",
            help="The action to take on extensions ('enable' or 'disable')"
        ),
    )

    def _change_extension_state(self, name, options):
        """Change the state of an extension."""
        extension, created = Extension.objects.get_or_create(name=name)
        newstate = options["action"] == "enable"
        if extension.enabled == newstate:
            return
        if newstate:
            extension.on()
        else:
            extension.off()

    def handle(self, *args, **options):
        """Entry point."""
        if "all" in args:
            for fullname in settings.MODOBOA_APPS:
                if not fullname.startswith("modoboa.extensions"):
                    continue
                extname = fullname.replace("modoboa.extensions.", "")
                self._change_extension_state(extname, options)
            return

        for extname in args:
            fullname = "modoboa.extensions.{}".format(extname)
            if not fullname in settings.MODOBOA_APPS:
                continue
            self._change_extension_state(extname, options)
