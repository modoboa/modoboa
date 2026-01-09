"""Async jobs definition."""

import logging
import os
import shutil

from modoboa.admin.app_settings import load_admin_settings
from modoboa.admin.models.mailbox import MailboxOperation
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools

logger = logging.getLogger("modoboa.jobs")


def rename_mailbox(operation):
    """Rename the mailbox folder through a RQ Job."""
    if not os.path.exists(operation.argument):
        logger.error(f"Failed to rename {operation.argument}, folder not found")
        operation.delete()
        return
    new_mail_home = operation.mailbox.mail_home
    dirname = os.path.dirname(new_mail_home)
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:
            reason = str(e).decode("utf-8")
            logger.critical(
                f"renaming of {operation.argument} to {new_mail_home} failed (reason: {reason})"
            )
            return
    code, output = exec_cmd(f"mv {operation.argument} {new_mail_home}")
    if code:
        logger.critical(f"Renaming of {new_mail_home} failed (reason: {output})")
        return
    operation.delete()


def delete_mailbox(operation):
    """Delete the mailbox folder through a RQ Job."""
    if not os.path.exists(operation.argument):
        logger.error(f"Failed to delete {operation.argument}, folder not found")
        operation.delete()
        return

    def onerror(function, path, excinfo):
        """Handle errors."""
        logger.critical(f"delete failed (reason: {excinfo})")
        operation.delete()

    shutil.rmtree(operation.argument, False, onerror)
    operation.delete()


def handle_mailbox_operations():
    load_admin_settings()
    if not param_tools.get_global_parameter("handle_mailboxes"):
        return
    for ope in MailboxOperation.objects.all():
        if ope.type == "rename":
            rename_mailbox(ope)
        elif ope.type == "delete":
            delete_mailbox(ope)
