import re
from modoboa.lib import parameters


class EmailSignature(object):
    """User signature

    :param user: User object
    """
    def __init__(self, user):
        self._sig = ""
        dformat = parameters.get_user(user, "EDITOR")
        content = parameters.get_user(user, "SIGNATURE")
        if len(content):
            getattr(self, "_format_sig_%s" % dformat)(content)

    def _format_sig_plain(self, content):
        self._sig = """
---
%s""" % content

    def _format_sig_html(self, content):
        content = re.sub("\n", "<br/>", content)
        self._sig = """<br/>
---<br/>
%s""" % content

    def __repr__(self):
        return self._sig
