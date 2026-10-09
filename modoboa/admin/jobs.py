"""Async jobs definition."""

import logging
import os
import shutil

from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext as _

import django_rq

from modoboa.admin import models
from modoboa.admin.app_settings import load_admin_settings
from modoboa.admin.dns_checker import DNSChecker
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools

logger = logging.getLogger("modoboa.jobs")


def rename_failed(operation, reason):
    """Raise an alarm and drop the operation so the mailbox stops being blocked."""
    mailbox = operation.mailbox
    logger.critical(
        f"renaming of {operation.argument} to {mailbox.mail_home} failed (reason: {reason})"
    )
    mailbox.alarms.create(
        domain=mailbox.domain,
        internal_name="mailbox_rename_failed",
        title=_("Failed to move mailbox folder {} to {} ({})").format(
            operation.argument, mailbox.mail_home, reason
        ),
    )
    operation.delete()


def rename_mailbox(operation):
    """Rename the mailbox folder through a RQ Job."""
    if not os.path.exists(operation.argument):
        logger.error(f"Failed to rename {operation.argument}, folder not found")
        operation.delete()
        return
    new_mail_home = operation.mailbox.mail_home
    if os.path.exists(new_mail_home):
        # mv would move the old folder inside the existing one
        rename_failed(operation, "destination already exists")
        return
    dirname = os.path.dirname(new_mail_home)
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:
            rename_failed(operation, str(e))
            return
    code, output = exec_cmd(["mv", operation.argument, new_mail_home])
    if code:
        rename_failed(operation, output.decode(errors="replace"))
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

    shutil.rmtree(operation.argument, False, onerror)
    operation.delete()


def handle_mailbox_operations():
    load_admin_settings()
    if not param_tools.get_global_parameter("handle_mailboxes"):
        # Pending operations would otherwise block their mailboxes forever
        models.MailboxOperation.objects.all().delete()
        return
    for ope in models.MailboxOperation.objects.all():
        if ope.type == "rename":
            rename_mailbox(ope)
        elif ope.type == "delete":
            delete_mailbox(ope)


def launch_domain_dns_checks(domain_id: int):
    domain = models.Domain.objects.get(id=domain_id)
    DNSChecker().run(domain)
    domain.last_dns_check_execution = timezone.now()
    domain.save(update_fields=["last_dns_check_execution"])


def handle_dns_checks():
    """Launch DNS checks for every possible domain."""
    minute = timezone.now().minute
    queue = django_rq.get_queue("modoboa")
    for domain in models.Domain.objects.annotate(slot=F("id") % 60).filter(
        enable_dns_checks=True, slot=minute
    ):
        if domain.uses_a_reserved_tld:
            continue
        queue.enqueue(launch_domain_dns_checks, domain.id)
