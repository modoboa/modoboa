# coding: utf-8

from django.utils.translation import ugettext as _
from managesieve import ManageSieveClient, Error
from modoboa.lib import ConnectionsManager, ConnectionError, parameters

class SieveClientError(Exception):
    pass

class SieveClient(object):
    __metaclass__ = ConnectionsManager

    def __init__(self, user=None, password=None):
        ret, msg = self.login(user, password)
        if not ret:
            raise ConnectionError(msg)

    def login(self, user, password):
        self.msc = ManageSieveClient(parameters.get_admin("SERVER"), 
                                     int(parameters.get_admin("PORT")),
                                     debug=False)
        use_starttls = True if parameters.get_admin("STARTTLS") == "yes" else False
        authmech = parameters.get_admin("AUTHENTICATION_MECH")
        if authmech == "AUTO":
            authmech = None
        if not self.msc.connect(user, password, use_starttls, authmech):
            return False, _("Connection to MANAGESIEVE server failed, check your configuration")
        return True, None
        
    def refresh(self, user, password):
        try:
            self.msc.capability()
        except Error, e:
            pass
        else:
            return
        ret, msg = self.login(user, password)
        if not ret:
            raise ConnectionError(msg)

    def listscripts(self):
        return self.msc.listscripts()

    def getscript(self, name):
        content = self.msc.getscript(name)
        if content is None:
            raise SieveClientError(self.msc.errmsg)
        return content

    def pushscript(self, name, content, active=False):
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
