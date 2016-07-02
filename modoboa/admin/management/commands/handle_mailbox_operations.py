
import logging
from optparse import make_option
import os

from django.core.management.base import BaseCommand

from modoboa.lib import parameters
from modoboa.lib.sysutils import exec_cmd
from modoboa.lib.exceptions import InternalError

from ...app_settings import load_admin_settings
from ...models import MailboxOperation


class OperationError(Exception):
    pass


class Command(BaseCommand):
    help = 'Handles rename and delete operations on mailboxes'

    option_list = BaseCommand.option_list + (
        make_option(
            '--pidfile', default='/tmp/handle_mailbox_operations.pid',
            help='Path to the file that will contain the PID of this process'
        ),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('modoboa.admin')

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
        if not os.path.exists(operation.argument):
            return
        code, output = exec_cmd(
            "rm -r %s" % operation.argument
        )
        if code:
            raise OperationError(output)

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
        with open(path, 'w') as fp:
            print >> fp, os.getpid()
        return True

    def handle(self, *args, **options):
        load_admin_settings()
        if parameters.get_admin("HANDLE_MAILBOXES") == 'no':
            return
        if not self.check_pidfile(options['pidfile']):
            return
        for ope in MailboxOperation.objects.all():
            try:
                f = getattr(self, '%s_mailbox' % ope.type)
            except AttributeError:
                continue
            try:
                f(ope)
            except (OperationError, InternalError) as e:
                self.logger.critical('%s failed (reason: %s)',
                                     ope, str(e).encode('utf-8'))
            else:
                self.logger.info('%s succeed', ope)
                ope.delete()
        os.unlink(options['pidfile'])
