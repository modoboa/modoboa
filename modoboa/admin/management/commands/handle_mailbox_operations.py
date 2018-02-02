# -*- coding: utf-8 -*-

"""A management command to apply mailbox operations."""

from __future__ import print_function, unicode_literals

import logging
import os
import shutil

from django.core.management.base import BaseCommand

from modoboa.lib.exceptions import InternalError
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools
from ...app_settings import load_admin_settings
from ...models import MailboxOperation


class OperationError(Exception):
    """Custom exception."""

    pass


class Command(BaseCommand):
    """Command definition"""

    help = "Handles rename and delete operations on mailboxes"  # NOQA:A003

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("modoboa.admin")

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--pidfile", default="/tmp/handle_mailbox_operations.pid",
            help="Path to the file that will contain the PID of this process"
        )

    def rename_mailbox(self, operation):
        if not os.path.exists(operation.argument):
            return
        new_mail_home = operation.mailbox.mail_home
        dirname = os.path.dirname(new_mail_home)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except os.error as e:
                raise OperationError(str(e))
        code, output = exec_cmd(
            "mv %s %s" % (operation.argument, new_mail_home)
        )
        if code:
            raise OperationError(output)

    def delete_mailbox(self, operation):
        """Try to delete a mailbox tree on filesystem."""
        if not os.path.exists(operation.argument):
            return

        def onerror(function, path, excinfo):
            """Handle errors."""
            self.logger.critical(
                "delete failed (reason: {})".format(excinfo))

        shutil.rmtree(operation.argument, False, onerror)

    def check_pidfile(self, path):
        """Check if this command is already running

        :param str path: path to the file containing the PID
        :return: a boolean, True means we can go further
        """
        if os.path.exists(path):
            with open(path) as fp:
                pid = fp.read().strip()
            code, output = exec_cmd(
                "grep handle_mailbox_operations /proc/%s/cmdline" % pid
            )
            if not code:
                return False
        with open(path, "w") as fp:
            print(os.getpid(), file=fp)
        return True

    def handle(self, *args, **options):
        """Command entry point."""
        load_admin_settings()
        if not param_tools.get_global_parameter("handle_mailboxes"):
            return
        if not self.check_pidfile(options["pidfile"]):
            return
        for ope in MailboxOperation.objects.all():
            try:
                f = getattr(self, "%s_mailbox" % ope.type)
            except AttributeError:
                continue
            try:
                f(ope)
            except (OperationError, InternalError) as e:
                self.logger.critical(
                    "%s failed (reason: %s)", ope, str(e).decode("utf-8"))
            else:
                self.logger.info("%s succeed", ope)
                ope.delete()
        os.unlink(options["pidfile"])
