import os
import logging
from optparse import make_option
from django.core.management.base import BaseCommand
from modoboa.lib import parameters
from modoboa.admin.models import MailboxOperation


class OperationError(Exception):
    pass


class Command(BaseCommand):
    args = ''
    help = 'Handles rename and delete operations on mailboxes'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('modoboa.cron')

    def rename_mailbox(self, operation):
        if not os.path.exists(operation.argument):
            return
        new_mail_home = operation.mailbox.mail_home.strip(os.sep)
        self.logger.info("Renaming %s to %s", operation.argument, new_mail_home)
        curpath = '/'
        for part in new_mail_home.split(os.sep)[:-1]:
            if not part:
                continue
            curpath = os.path.join(curpath, part)
            if not os.path.exists(curpath):
                os.mkdir(curpath)
        code, output = exec_cmd(
            "mv %s %s" % (old_mail_home, new_mail_home)
        )
        if code:
            raise OperationError(output)

    def delete_mailbox(self, operation):
        if not os.path.exists(operation.argument):
            return
        self.logger.info("Deleting %s", operation.argument)
        code, output = exec_cmd(
            "rm -r %s" % operation.argument
        )
        if code:
            raise OperationError(output)

    def handle(self):
        if parameters.get_admin("HANDLE_MAILBOXES") == 'no':
            return
        for ope in MailboxOperation.objects.all():
            try:
                f = getattr(self, '%s_mailbox' % ope.optype)
            except AttributeError:
                continue
            try:
                f(ope)
            except OperationError as e:
                self.logger.critical('Operation failed: %s', str(e))
            else:
                ope.delete()
