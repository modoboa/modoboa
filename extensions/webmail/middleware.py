# coding: utf-8

from modoboa.lib.webutils import ajax_response
from modoboa.extensions.webmail.lib import WebmailError

class WebmailErrorMiddleware(object):
    def process_exception(self, request, exception):
        if not isinstance(exception, WebmailError):
            return None
        return ajax_response(request, status="ko", 
                             respmsg=str(exception), norefresh=True)
