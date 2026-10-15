"""Internal tools."""

import logging
import re

from sievelib.factory import FiltersSet
from sievelib import managesieve
from sievelib.parser import Parser

from django.utils.translation import gettext as _

from modoboa.lib.exceptions import ModoboaException
from modoboa.parameters import tools as param_tools

from . import constants

logger = logging.getLogger("modoboa.sievefilters")


class SieveClientError(ModoboaException):
    http_code = 400


class SieveScriptNotFound(SieveClientError):
    http_code = 404


class SieveScriptParseError(SieveClientError):
    pass


class UnsupportedSieveFilter(Exception):
    """Filter that can't be represented with condition and action templates."""


class SieveActionTemplateNotFound(UnsupportedSieveFilter):
    pass


class SieveClient:
    """Sieve client."""

    msc: managesieve.Client

    def __init__(self, user: str | None = None, password: str | None = None):
        if user and password:
            try:
                ret, msg = self.login(user, password)
            except managesieve.Error as e:
                raise SieveClientError(str(e)) from None
            if not ret:
                raise SieveClientError(msg)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.logout()

    @property
    def errmsg(self) -> str:
        return self.msc.errmsg.decode() or _("ManageSieve server returned an error")

    def login(self, user: str, password: str) -> tuple[bool, str | None]:
        conf = dict(param_tools.get_global_parameters("sievefilters"))
        self.msc = managesieve.Client(conf["server"], conf["port"], debug=False)
        try:
            ret = self.msc.connect(
                user, password, starttls=conf["starttls"], authmech="OAUTHBEARER"
            )
        except managesieve.Error as err:
            logger.error("ManageSieve connection failed: %s", err)
            ret = False
        if not ret:
            return False, _(
                "Connection to MANAGESIEVE server failed, check your " "configuration"
            )
        return True, None

    def logout(self):
        try:
            self.msc.logout()
        except (managesieve.Error, OSError):
            # Connection already lost, nothing to close properly
            pass
        self.msc = None

    def listscripts(self) -> tuple[str | None, list[str]]:
        result = self.msc.listscripts()
        if result is None:
            raise SieveClientError(self.errmsg)
        return result

    def getscript(self, name: str, format: str = "raw") -> FiltersSet | str:
        content = self.msc.getscript(name)
        if content is None:
            raise SieveScriptNotFound(
                self.msc.errmsg.decode() or _("Filter set %s not found") % name
            )
        if format == "raw":
            return content
        p = Parser()
        if not p.parse(content):
            raise SieveScriptParseError(p.error)
        fs = FiltersSet(name)
        fs.from_parser_result(p)
        return fs

    def pushscript(self, name: str, content: str, active: bool = False) -> None:
        # Size in bytes, as sent by putscript which normalizes line breaks
        size = len(re.sub(r"\r?\n", "\r\n", content).encode("utf-8"))
        if not self.msc.havespace(name, size):
            error = "{} ({})".format(_("Not enough space on server"), self.errmsg)
            raise SieveClientError(error)
        if not self.msc.putscript(name, content):
            raise SieveClientError(self.errmsg)
        if active and not self.msc.setactive(name):
            raise SieveClientError(self.errmsg)

    def deletescript(self, name: str):
        if not self.msc.deletescript(name):
            raise SieveClientError(self.errmsg)

    def activatescript(self, name: str):
        if not self.msc.setactive(name):
            raise SieveClientError(self.errmsg)


def find_action_template(action: str):
    """Find template corresponding to action."""
    for tpl in constants.ACTION_TEMPLATES:
        if tpl["name"] == action:
            return tpl
    raise SieveActionTemplateNotFound(f"action {action} not defined")
