"""Script to register RQ jobs."""


def rename_mailbox(op_id):
    """Rename the mailbox folder through a RQ Job."""
    import logging
    import os

    from modoboa.admin.app_settings import load_admin_settings
    from modoboa.admin.models.mailbox import MailboxOperation
    from modoboa.lib.sysutils import exec_cmd
    from modoboa.parameters import tools as param_tools

    logger = logging.getLogger("modoboa.admin")

    load_admin_settings()
    if not param_tools.get_global_parameter("handle_mailboxes"):
        return
    try:
        operation = MailboxOperation.objects.get(pk=op_id)
    except MailboxOperation.DoesNotExist:
        logger.error(f"Failed to retrieve operation id {op_id} for renaming")
        return
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


def delete_mailbox(op_id):
    """Delete the mailbox folder through a RQ Job."""
    import logging
    import os
    import shutil

    from modoboa.admin.app_settings import load_admin_settings
    from modoboa.admin.models.mailbox import MailboxOperation
    from modoboa.parameters import tools as param_tools

    logger = logging.getLogger("modoboa.admin")

    load_admin_settings()
    if not param_tools.get_global_parameter("handle_mailboxes"):
        return

    try:
        operation = MailboxOperation.objects.get(pk=op_id)
    except MailboxOperation.DoesNotExist:
        logger.error(f"Failed to retrieve operation id {op_id} for deletion")
        return

    if not os.path.exists(operation.argument):
        logger.error(f"Failed to delete {operation.argument}, folder not found")
        operation.delete()
        return

    def onerror(function, path, excinfo):
        import logging

        """Handle errors."""
        logger = logging.getLogger("modoboa.admin")
        logger.critical(f"delete failed (reason: {excinfo})")
        operation.delete()

    shutil.rmtree(operation.argument, False, onerror)
    operation.delete()


def handle_remaining_operation():
    import logging

    import django_rq

    from modoboa.parameters import tools as param_tools
    from modoboa.admin.app_settings import load_admin_settings
    from modoboa.admin.models.mailbox import MailboxOperation

    load_admin_settings()
    if not param_tools.get_global_parameter("handle_mailboxes"):
        return
    queue = django_rq.get_queue("dovecot")
    if queue.started_job_registry.count > 0 or queue.scheduled_job_registry.count > 0:
        return
    logger = logging.getLogger("modoboa.admin")
    for ope in MailboxOperation.objects.all():
        if ope.type == "rename":
            rename_mailbox(ope.pk)
        elif ope.type == "delete":
            delete_mailbox(ope.pk)
