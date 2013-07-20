# coding: utf-8
import getpass
import inspect
import os
from django.template import Context, Template
from modoboa.core.management import Command


class MapFile(object):
    category = 'std'

    def __init__(self):
        self.base_tpl = Template("""user = {{ dbuser }}
password = {{ dbpassword }}
dbname = {{ dbname }}
hosts = {{ dbhost }}
query = {{ query|safe }}
""")

    def render(self, destdir, dbtype, **options):
        try:
            options['query'] = getattr(self, dbtype)
        except AttributeError:
            return

        content = self.base_tpl.render(Context(options))
        fp = open("%s/%s" % (destdir, self.filename), "w")
        fp.write(content)
        fp.close()


class DomainsMap(MapFile):
    filename = 'sql-domains.cf'
    mysql = "SELECT name FROM admin_domain WHERE name='%s' AND enabled=1"
    postgres = "SELECT name FROM admin_domain WHERE name='%s' AND enabled"


class DomainsAliasesMap(MapFile):
    filename = 'sql-domain-aliases.cf'
    mysql = "SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1"
    postgres = "SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled AND dom.enabled"


class MailboxesMap(MapFile):
    filename = 'sql-mailboxes.cf'
    mysql = "SELECT 1 FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_user user ON mb.user_id=user.id WHERE dom.enabled=1 AND dom.name='%d' AND user.is_active=1 AND mb.address='%u'"
    postgres = "SELECT 1 FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN admin_user u ON mb.user_id=u.id WHERE dom.enabled AND dom.name='%d' AND u.is_active AND mb.address='%u'"


class AliasesMap(MapFile):
    filename = 'sql-aliases.cf'
    mysql = "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT concat(al.address, '@', dom.name) FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.id IN (SELECT al_al.to_alias_id FROM admin_alias_aliases al_al INNER JOIN admin_alias al ON al_al.from_alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1 AND al.extmboxes<>'')"
    postgres = "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled)) UNION (SELECT al.address || '@' || dom.name FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.id IN (SELECT al_al.to_alias_id FROM admin_alias_aliases al_al INNER JOIN admin_alias al ON al_al.from_alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled AND al.address='%u' AND al.enabled AND al.extmboxes<>'')"


class DomainAliasesMailboxesMap(MapFile):
    filename = 'sql-domain-aliases-mailboxes.cf'
    mysql = "SELECT DISTINCT concat(mb.address, '@', dom.name) FROM admin_alias al INNER JOIN admin_domain dom ON dom.id=al.domain_id INNER JOIN admin_domainalias domal ON domal.target_id=dom.id INNER JOIN (admin_alias_mboxes almb, admin_mailbox mb) ON (almb.alias_id=al.id AND almb.mailbox_id=mb.id) WHERE domal.name='%d' AND domal.enabled=1 AND (al.address='%u' OR mb.address='%u')"
    postgres = "SELECT DISTINCT mb.address || '@' || dom.name FROM admin_alias al INNER JOIN admin_domain dom ON dom.id=al.domain_id INNER JOIN admin_domainalias domal ON domal.target_id=dom.id INNER JOIN admin_alias_mboxes almb ON almb.alias_id=al.id INNER JOIN admin_mailbox mb ON almb.mailbox_id=mb.id WHERE domal.name='%d' AND domal.enabled AND (al.address='%u' OR mb.address='%u')"


class CatchallAliasesMap(MapFile):
    filename = 'sql-catchall-aliases.cf'
    mysql = "(SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled=1 AND al.address='*' AND dom.name='%d' AND dom.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled='1' AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled=1)"
    postgres = "(SELECT mb.address || '@' || dom.name FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled AND al.address='*' AND dom.name='%d' AND dom.enabled)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled)"


class TransportMap(MapFile):
    category = "autoreply"
    filename = 'sql-transport.cf'
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"


class AutoRepliesMap(MapFile):
    category = "autoreply"
    filename = 'sql-autoreplies.cf'
    mysql = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"
    postgres = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"


class PostfixMapsCommand(Command):
    help = "Generate ready-to-use postfix map files"

    def __init__(self, *args, **kwargs):
        super(PostfixMapsCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument('destdir', type=str,
                                  help='Directory that will contain generated map files')
        self._parser.add_argument('--dbtype', type=str, choices=['mysql', 'postgres'], default='mysql',
                                  help='Used database type')
        self._parser.add_argument('--dbhost', type=str, default='127.0.0.1',
                                  help='Database host address')
        self._parser.add_argument('--categories', type=str, nargs='*', default=['std'],
                                  help='Map file categories to generate (choices: std, autoreply)')

    def handle(self, parsed_args):
        dbname = raw_input('Database name: ')
        dbuser = raw_input('Username: ')
        dbpass = getpass.getpass('Password: ')

        try:
            os.mkdir(parsed_args.destdir)
        except OSError:
            pass

        for k, v in globals().iteritems():
            if not inspect.isclass(v) or not issubclass(v, MapFile):
                continue
            if not v.category in parsed_args.categories:
                continue
            v().render(parsed_args.destdir, parsed_args.dbtype,
                       dbname=dbname, dbuser=dbuser, dbpassword=dbpass,
                       dbhost=parsed_args.dbhost)
