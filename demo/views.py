# coding: utf-8
from django.contrib.auth.decorators import login_required
from modoboa.admin.lib import is_not_localadmin
from modoboa.lib.webutils import ajax_response
from modoboa.lib.emailutils import sendmail_simple

@login_required
@is_not_localadmin()
def send_virus(request):
    status, error = sendmail_simple("virus@evil.tld", request.user.username, """
This is the EICAR testvirus pattern.

X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*

It cannot harm your computer, but virus scanners
will detect and treat it as if it were a virus.
""")
    if status:
        return ajax_response(request)
    return ajax_response(request, "ko", respmsg=error)

@login_required
@is_not_localadmin()
def send_spam(request):
    status, error = sendmail_simple("spam@evil.tld", request.user.username, """
This is the GTUBE, the
        Generic
        Test for
        Unsolicited
        Bulk
        Email

If your spam filter supports it, the GTUBE provides a test by which you
can verify that the filter is installed correctly and is detecting incoming
spam. You can send yourself a test mail containing the following string of
characters (in upper case and with no white spaces and line breaks):

XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X

You should send this test mail from an account outside of your network.
""")
    if status:
        return ajax_response(request)
    return ajax_response(request, "ko", respmsg=error)
