import re
from modoboa.lib import parameters


class EmailSignature(object):
    """User signature

    :param user: User object
    """
    def __init__(self, user):
        self._sig = u""
        dformat = parameters.get_user(user, "EDITOR")
        content = parameters.get_user(user, "SIGNATURE")
        if len(content):
            getattr(self, "_format_sig_%s" % dformat)(content)

    def _format_sig_plain(self, content):
        self._sig = u"""
---
%s""" % content

    def _format_sig_html(self, content):
        content = re.sub("\n", "<br/>", content)
        self._sig = u"""<br/>
---<br/>
%s""" % content

    def __unicode__(self):
        return self._sig
