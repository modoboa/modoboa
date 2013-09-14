import os
import logging
from optparse import make_option
from django.core.management.base import BaseCommand
from modoboa.lib import parameters
from modoboa.lib.sysutils import exec_cmd
from modoboa.admin import AdminConsole
from modoboa.admin.exceptions import AdminError
from modoboa.admin.models import MailboxOperation


class OperationError(Exception):
    pass


class Command(BaseCommand):
    args = ''
    help = 'Handles rename and delete operations on mailboxes'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('modoboa.admin')

    def rename_mailbox(self, operation):
        if not os.path.exists(operation.argument):
            return
        new_mail_home = operation.mailbox.mail_home
        if not os.path.exists(new_mail_home):
            try:
                os.makedirs(os.path.dirname(new_mail_home))
            except os.error as e:
                raise OperationError(str(e))
        code, output = exec_cmd(
            "mv %s %s" % (ope.argument, new_mail_home)
        )
        if code:
            raise OperationError(output)

    def delete_mailbox(self, operation):
        if not os.path.exists(operation.argument):
            return
        code, output = exec_cmd(
            "rm -r %s" % operation.argument
        )
        if code:
            raise OperationError(output)

    def handle(self, *args, **options):
        AdminConsole().load()
        if parameters.get_admin("HANDLE_MAILBOXES") == 'no':
            return
        for ope in MailboxOperation.objects.all():
            try:
                f = getattr(self, '%s_mailbox' % ope.type)
            except AttributeError:
                continue
            try:
                f(ope)
            except (OperationError, AdminError) as e:
                self.logger.critical('%s failed (reason: %s)', ope, e)
            else:
                self.logger.info('%s succeed', ope)
                ope.delete()
