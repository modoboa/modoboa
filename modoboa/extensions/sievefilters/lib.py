# coding: utf-8

from django.utils.translation import ugettext as _
from sievelib.managesieve import Client, Error
from sievelib.parser import Parser
from sievelib.factory import FiltersSet
from modoboa.lib import parameters
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.connections import ConnectionsManager, ConnectionError


class SieveClientError(ModoboaException):
    http_code = 424


class SieveClient(object):
    __metaclass__ = ConnectionsManager

    def __init__(self, user=None, password=None):
        try:
            ret, msg = self.login(user, password)
        except Error, e:
            raise ConnectionError(str(e))
        if not ret:
            raise ConnectionError(msg)

    def login(self, user, password):
        self.msc = Client(parameters.get_admin("SERVER"),
                          int(parameters.get_admin("PORT")),
                          debug=False)
        use_starttls = True if parameters.get_admin("STARTTLS") == "yes" \
            else False
        authmech = parameters.get_admin("AUTHENTICATION_MECH")
        if authmech == "AUTO":
            authmech = None
        try:
            ret = self.msc.connect(user, password, use_starttls, authmech)
        except Error:
            ret = False
        if not ret:
            return False, _("Connection to MANAGESIEVE server failed, check your configuration")
        return True, None

    def logout(self):
        self.msc.logout()
        self.msc = None

    def refresh(self, user, password):
        import ssl

        if self.msc is not None:
            try:
                self.msc.capability()
            except Error, e:
                pass
            else:
                return
        try:
            ret, msg = self.login(user, password)
        except (Error, ssl.SSLError), e:
            raise ConnectionError(e)
        if not ret:
            raise ConnectionError(msg)

    def listscripts(self):
        return self.msc.listscripts()

    def getscript(self, name, format="raw"):
        content = self.msc.getscript(name)
        if content is None:
            raise SieveClientError(self.msc.errmsg)
        if format == "raw":
            return content
        p = Parser()
        if not p.parse(content):
            print "Parse error????"
            return None
        fs = FiltersSet(name)
        fs.from_parser_result(p)
        return fs

    def pushscript(self, name, content, active=False):
        if type(content) is unicode:
            content = content.encode("utf-8")
        if not self.msc.havespace(name, len(content)):
            error = "%s (%s)" % (_("Not enough space on server"), self.msc.errmsg)
            raise SieveClientError(error)
        if not self.msc.putscript(name, content):
            raise SieveClientError(self.msc.errmsg)
        if active and not self.msc.setactive(name):
            raise SieveClientError(self.msc.errmsg)

    def deletescript(self, name):
        if not self.msc.deletescript(name):
            raise SieveClientError(self.msc.errmsg)

    def activatescript(self, name):
        if not self.msc.setactive(name):
            raise SieveClientError(self.msc.errmsg)
