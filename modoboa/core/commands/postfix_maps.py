# coding: utf-8
import getpass
import inspect
import os
import sys
import datetime
from django.template import Context, Template
from . import Command


class MapFilesGenerator(object):

    def __init__(self):
        self.template = Template("""user = {{ dbuser }}
password = {{ dbpass }}
dbname = {{ dbname }}
hosts = {{ dbhost }}
query = {{ query|safe }}
""")
        self.tpl_context = {
            'dbhost': raw_input('Database host: '),
            'dbname': raw_input('Database name: '),
            'dbuser': raw_input('Username: '),
            'dbpass': getpass.getpass('Password: ')
        }
        if not self.tpl_context['dbhost']:
            self.tpl_context['dbhost'] = '127.0.0.1'

    def render(self, args):
        """Render all map files.

        :param args: arguments received from the command line
        """
        try:
            os.mkdir(args.destdir)
        except OSError:
            pass

        for v in globals().values():
            if not inspect.isclass(v) or not issubclass(v, MapFile):
                continue
            if v is MapFile:
                continue
            if not v.category in args.categories:
                continue
            content = self.template.render(
                Context(dict(self.tpl_context.items(),
                             query=getattr(v, args.dbtype)))
            )
            with open("%s/%s" % (args.destdir, v.filename), "w") as fp:
                print >> fp, """# This file was generated on %s by running:
# %s %s
# DO NOT EDIT!
""" % (datetime.datetime.now().isoformat(),
       os.path.basename(sys.argv[0]),
       ' '.join(sys.argv[1:]))
                print >> fp, content


class SQLiteMapFilesGenerator(MapFilesGenerator):

    def __init__(self):
        self.template = Template("""dbpath = {{ dbpath }}
query = {{ query|safe }}
""")
        self.tpl_context = {
            'dbpath': raw_input('Database path: ')
        }


class MapFile(object):
    category = 'std'


class DomainsMap(MapFile):
    filename = 'sql-domains.cf'
    mysql = "SELECT name FROM admin_domain WHERE name='%s' AND enabled=1"
    postgres = "SELECT name FROM admin_domain WHERE name='%s' AND enabled"
    sqlite = "SELECT name FROM admin_domain WHERE name='%s' AND enabled=1"


class DomainsAliasesMap(MapFile):
    filename = 'sql-domain-aliases.cf'
    mysql = "SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1"
    postgres = "SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled AND dom.enabled"
    sqlite = "SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1"


class MailboxesMap(MapFile):
    filename = 'sql-mailboxes.cf'
    mysql = "SELECT 1 FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_user user ON mb.user_id=user.id WHERE dom.enabled=1 AND dom.name='%d' AND user.is_active=1 AND mb.address='%u'"
    postgres = "SELECT 1 FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_user u ON mb.user_id=u.id WHERE dom.enabled AND dom.name='%d' AND u.is_active AND mb.address='%u'"
    sqlite = "SELECT 1 FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_user user ON mb.user_id=user.id WHERE dom.enabled=1 AND dom.name='%d' AND user.is_active=1 AND mb.address='%u'"


class AliasesMap(MapFile):
    filename = 'sql-aliases.cf'
    mysql = "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT concat(al.address, '@', dom.name) FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.id IN (SELECT al_al.to_alias_id FROM admin_alias_aliases al_al INNER JOIN admin_alias al ON al_al.from_alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1 AND al.extmboxes<>'')"
    postgres = "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled)) UNION (SELECT al.address || '@' || dom.name FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.id IN (SELECT al_al.to_alias_id FROM admin_alias_aliases al_al INNER JOIN admin_alias al ON al_al.from_alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled AND al.extmboxes<>'')"
    sqlite = "(SELECT (mb.address || '@' || dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT (al.address || '@' || dom.name) FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.id IN (SELECT al_al.to_alias_id FROM admin_alias_aliases al_al INNER JOIN admin_alias al ON al_al.from_alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1 AND al.extmboxes<>'')"


class DomainAliasesMailboxesMap(MapFile):
    filename = 'sql-domain-aliases-mailboxes.cf'
    mysql = "(SELECT concat(mb.address, '@', dom.name) FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_mailbox mb ON mb.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled=1 AND mb.address='%u') UNION (SELECT concat(al.address, '@', dom.name) FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_alias al ON al.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled=1 AND al.address='%u')"
    postgres = "(SELECT mb.address || '@' || dom.name FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_mailbox mb ON mb.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled AND mb.address='%u') UNION (SELECT al.address || '@' || dom.name FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_alias al ON al.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled AND al.address='%u')"
    sqlite = "(SELECT mb.address || '@' || dom.name FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_mailbox mb ON mb.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled=1 AND mb.address='%u') UNION (SELECT al.address || '@' || dom.name FROM admin_domainalias domal INNER JOIN admin_domain dom ON domal.target_id=dom.id INNER JOIN admin_alias al ON al.domain_id=dom.id WHERE domal.name='%d' AND dom.enabled=1 AND al.address='%u')"


class CatchallAliasesMap(MapFile):
    filename = 'sql-catchall-aliases.cf'
    mysql = "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled=1 AND al.address='*' AND dom.name='%d' AND dom.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled='1' AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled=1)"
    postgres = "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled AND al.address='*' AND dom.name='%d' AND dom.enabled)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled)"
    sqlite = "(SELECT (mb.address || '@' || dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled=1 AND al.address='*' AND dom.name='%d' AND dom.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled='1' AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled=1)"


class MaintainMap(MapFile):
    filename = 'sql-maintain.cf'
    mysql = "SELECT '450 Requested mail action not taken: mailbox unavailable' FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' LIMIT 1"
    postgres = "SELECT '450 Requested mail action not taken: mailbox unavailable' FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' LIMIT 1"
    sqlite = "SELECT '450 Requested mail action not taken: mailbox unavailable' FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_mailboxoperation mbop ON mbop.mailbox_id=mb.id WHERE dom.name='%d' AND mb.address='%u' LIMIT 1"


class TransportMap(MapFile):
    category = "autoreply"
    filename = 'sql-transport.cf'
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    sqlite = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"


class AutoRepliesMap(MapFile):
    category = "autoreply"
    filename = 'sql-autoreplies.cf'
    mysql = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"
    postgres = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"
    sqlite = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"


class PostfixMapsCommand(Command):
    help = "Generate ready-to-use postfix map files"

    def __init__(self, *args, **kwargs):
        super(PostfixMapsCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument(
            'destdir', type=str,
            help='Directory that will contain generated map files'
        )
        self._parser.add_argument(
            '--dbtype', type=str, choices=['mysql', 'postgres', 'sqlite'],
            default='mysql',
            help='Used database type'
        )
        self._parser.add_argument(
            '--categories', type=str, nargs='*', default=['std'],
            help='Map file categories to generate (choices: std, autoreply)'
        )

    def handle(self, parsed_args):
        if parsed_args.dbtype == 'sqlite':
            g = SQLiteMapFilesGenerator()
        else:
            g = MapFilesGenerator()
        g.render(parsed_args)
