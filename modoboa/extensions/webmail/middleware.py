# coding: utf-8
from modoboa.lib.webutils import ajax_response, _render_error
from modoboa.extensions.webmail.exceptions import WebmailError, ImapError

class WebmailErrorMiddleware(object):
    def process_exception(self, request, exception):
        if not isinstance(exception, (WebmailError, ImapError)):
            return None
        json = request.GET.get("json", False) if request.method == "GET" \
            else request.POST.get("json", False)
        if json:
            return ajax_response(request, status="ko",
                                 respmsg=str(exception), norefresh=True)
        return _render_error(request, user_context=dict(error=str(exception)))
