# coding: utf-8
import getpass
import inspect
import os
import sys
import datetime
from django.template import Context, Template
from . import Command


class MapFilesGenerator(object):

    def __init__(self, dbinfo=None):
        """Constructor.
        """
        self.template = Template("""user = {{ dbuser }}
password = {{ dbpass }}
dbname = {{ dbname }}
hosts = {{ dbhost }}
query = {{ query|safe }}
""")
        if dbinfo is None:
            self.tpl_context = {
                'dbhost': raw_input('Database host: '),
                'dbname': raw_input('Database name: '),
                'dbuser': raw_input('Username: '),
                'dbpass': getpass.getpass('Password: ')
            }
        else:
            self.tpl_context = {
                'dbhost': dbinfo['HOST'],
                'dbname': dbinfo['NAME'],
                'dbuser': dbinfo['USER'],
                'dbpass': dbinfo['PASSWORD']
            }
        if not self.tpl_context['dbhost']:
            self.tpl_context['dbhost'] = '127.0.0.1'

    def __render_map(self, args, mapobject):
        """Render a map file.

        :param args: command line arguments
        :param mapobject: a ``MapFile`` subclass
        """
        content = self.template.render(
            Context(dict(
                self.tpl_context.items(),
                query=getattr(mapobject, args.dbtype)
            ))
        )
        with open("%s/%s" % (args.destdir, mapobject.filename), "w") as fp:
            print >> fp, """# This file was generated on %s by running:
# %s %s
# DO NOT EDIT!
""" % (datetime.datetime.now().isoformat(),
       os.path.basename(sys.argv[0]),
       ' '.join(sys.argv[1:]))
            print >> fp, content

    def __render_std_maps(self, args):
        """Render standard map files.

        (ie. the ones belonging to the 'std' category)

        :param args: command line arguments
        """
        for v in globals().values():
            if not inspect.isclass(v) or not issubclass(v, MapFile):
                continue
            if v is MapFile:
                continue
            if not v.category in args.categories:
                continue
            self.__render_map(args, v)

    def render(self, args):
        """Render all map files.

        :param args: arguments received from the command line
        """
        try:
            os.mkdir(args.destdir)
        except OSError:
            pass
        self.__render_std_maps(args)


class SQLiteMapFilesGenerator(MapFilesGenerator):

    def __init__(self, dbinfo=None):
        self.template = Template("""dbpath = {{ dbpath }}
query = {{ query|safe }}
""")
        if dbinfo is None:
            self.tpl_context = {
                'dbpath': raw_input('Database path: ')
            }
        else:
            self.tpl_context = {
                'dbpath': dbinfo['NAME']
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


class MailboxesSelfAliasesMap(MapFile):
    filename = "sql-mailboxes-self-aliases.cf"
    mysql = "SELECT email FROM core_user u INNER JOIN admin_mailbox mb ON mb.user_id=u.id WHERE u.email='%s' AND u.is_active=1"
    postgres = "SELECT email FROM core_user u INNER JOIN admin_mailbox mb ON mb.user_id=u.id WHERE u.email='%s' AND u.is_active"
    sqlite = "SELECT email FROM core_user u INNER JOIN admin_mailbox mb ON mb.user_id=u.id WHERE u.email='%s' AND u.is_active=1"


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
    filename = 'sql-autoreplies-transport.cf'
    mysql = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    postgres = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"
    sqlite = "SELECT method FROM postfix_autoreply_transport WHERE domain='%s'"


class AutoRepliesMap(MapFile):
    category = "autoreply"
    filename = 'sql-autoreplies.cf'
    mysql = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"
    postgres = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"
    sqlite = "SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'"


class RelayDomainsMap(MapFile):
    category = "relaydomains"
    filename = "sql-relaydomains.cf"
    mysql = "SELECT name FROM postfix_relay_domains_relaydomain WHERE name='%s' AND enabled=1"
    postgres = "SELECT name FROM postfix_relay_domains_relaydomain WHERE name='%s' AND enabled"
    sqlite = "SELECT name FROM postfix_relay_domains_relaydomain WHERE name='%s' AND enabled=1"


class RelayDomainsTransportMap(MapFile):
    category = "relaydomains"
    filename = "sql-relaydomains-transport.cf"
    mysql = "SELECT CONCAT(srv.name, ':[', rdom.target_host, ']') FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id WHERE rdom.enabled=1 AND rdom.name='%s'"
    postgres = "SELECT srv.name || ':[' || rdom.target_host || ']' FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id WHERE rdom.enabled AND rdom.name='%s'"
    sqlite = "SELECT srv.name || ':[' || rdom.target_host || ']' FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id WHERE rdom.enabled=1 AND rdom.name='%s'"


class RelayDomainAliasesTransportMap(MapFile):
    category = "relaydomains"
    filename = "sql-relaydomain-aliases-transport.cf"
    mysql = "SELECT CONCAT(srv.name, ':[', rdom.target_host, ']') FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id INNER JOIN postfix_relay_domains_relaydomainalias AS rdomalias ON rdom.id=rdomalias.target_id WHERE rdom.enabled=1 AND rdomalias.enabled=1 AND rdomalias.name='%s'"
    postgres = "SELECT srv.name || ':[' || rdom.target_host || ']' FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id INNER JOIN postfix_relay_domains_relaydomainalias AS rdomalias ON rdom.id=rdomalias.target_id WHERE rdom.enabled AND rdomalias.enabled AND rdomalias.name='%s'"
    sqlite = "SELECT srv.name || ':[' || rdom.target_host || ']' FROM postfix_relay_domains_service AS srv INNER JOIN postfix_relay_domains_relaydomain AS rdom ON rdom.service_id=srv.id INNER JOIN postfix_relay_domains_relaydomainalias AS rdomalias ON rdom.id=rdomalias.target_id WHERE rdom.enabled=1 AND rdomalias.enabled=1 AND rdomalias.name='%s'"


class RelayRecipientVerification(MapFile):
    category = "relaydomains"
    filename = "sql-relay-recipient-verification.cf"
    mysql = "SELECT 'reject_unverified_recipient' FROM postfix_relay_domains_relaydomain WHERE verify_recipients=1 AND name='%d'"
    postgres = "SELECT 'reject_unverified_recipient' FROM postfix_relay_domains_relaydomain WHERE verify_recipients AND name='%d'"
    sqlite = "SELECT 'reject_unverified_recipient' FROM postfix_relay_domains_relaydomain WHERE verify_recipients=1 AND name='%d'"


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
            '--dburl', type=str, nargs=1, default=None,
            help="url of Modoboa's database"
        )
        self._parser.add_argument(
            '--categories', type=str, nargs='*', default=['std'],
            help='Map file categories to generate (choices: std, autoreply)'
        )

    def handle(self, parsed_args):
        """Command entry point.
        """
        dbinfo = None
        if parsed_args.dburl:
            import dj_database_url
            dbinfo = dj_database_url.config(default=parsed_args.dburl[0])
            if 'sqlite' in dbinfo['ENGINE']:
                parsed_args.dbtype = 'sqlite'
            elif 'psycopg2' in dbinfo['ENGINE']:
                parsed_args.dbtype = 'postgres'
            else:
                parsed_args.dbtype = 'mysql'
        if parsed_args.dbtype == 'sqlite':
            g = SQLiteMapFilesGenerator(dbinfo)
        else:
            g = MapFilesGenerator(dbinfo)
        g.render(parsed_args)
