"""Internal tools."""

from typing import Optional, Tuple, Union

from sievelib.factory import FiltersSet
from sievelib import managesieve
from sievelib.parser import Parser

from django.utils.translation import gettext as _

from modoboa.lib.connections import ConnectionError
from modoboa.lib.exceptions import ModoboaException
from modoboa.parameters import tools as param_tools

from . import constants


class SieveClientError(ModoboaException):
    http_code = 400


class SieveActionTemplateNotFound(Exception):
    pass


class SieveClient:
    """Sieve client."""

    msc: managesieve.Client

    def __init__(self, user: Optional[str] = None, password: Optional[str] = None):
        if user and password:
            try:
                ret, msg = self.login(user, password)
            except (managesieve.Error, ConnectionError) as e:
                raise SieveClientError(str(e)) from None
            if not ret:
                raise SieveClientError(msg)

    def login(self, user: str, password: str) -> Tuple[bool, Union[str, None]]:
        conf = dict(param_tools.get_global_parameters("sievefilters"))
        self.msc = managesieve.Client(conf["server"], conf["port"], debug=True)
        try:
            ret = self.msc.connect(
                user, password, starttls=conf["starttls"], authmech="OAUTHBEARER"
            )
        except managesieve.Error as err:
            print(err)
            ret = False
        if not ret:
            return False, _(
                "Connection to MANAGESIEVE server failed, check your " "configuration"
            )
        return True, None

    def logout(self):
        self.msc.logout()
        self.msc = None

    def listscripts(self):
        return self.msc.listscripts()

    def getscript(self, name: str, format: str = "raw") -> Union[FiltersSet, str, None]:
        content = self.msc.getscript(name)
        if content is None:
            raise SieveClientError(self.msc.errmsg.decode())
        if format == "raw":
            return content
        p = Parser()
        if not p.parse(content):
            print("Parse error????")
            return None
        fs = FiltersSet(name)
        fs.from_parser_result(p)
        return fs

    def pushscript(self, name: str, content: str, active: bool = False) -> None:
        if not self.msc.havespace(name, len(content)):
            error = "{} ({})".format(_("Not enough space on server"), self.msc.errmsg)
            raise SieveClientError(error)
        if not self.msc.putscript(name, content):
            raise SieveClientError(self.msc.errmsg.decode())
        if active and not self.msc.setactive(name):
            raise SieveClientError(self.msc.errmsg)

    def deletescript(self, name: str):
        if not self.msc.deletescript(name):
            raise SieveClientError(self.msc.errmsg.decode())

    def activatescript(self, name: str):
        if not self.msc.setactive(name):
            raise SieveClientError(self.msc.errmsg.decode())


def find_action_template(action: str):
    """Find template corresponding to action."""
    for tpl in constants.ACTION_TEMPLATES:
        if tpl["name"] == action:
            return tpl
    raise SieveActionTemplateNotFound(f"action {action} not defined")
