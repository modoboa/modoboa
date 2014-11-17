# coding: utf-8
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import render_to_json_response
from modoboa.lib.emailutils import sendmail_simple, sendmail_fromfile
from modoboa.extensions.admin.lib import needs_mailbox


@login_required
@needs_mailbox()
def send_virus(request):
    status, error = sendmail_fromfile(
        "virus@example.net", request.user.username,
        os.path.join(settings.MODOBOA_DIR, "tmp/virus.msg")
    )
    if status:
        return render_to_json_response(_("Message sent"))
    return render_to_json_response(error, status=500)


@login_required
@needs_mailbox()
def send_spam(request):
    status, error = sendmail_simple(
        "spam@example.net", request.user.username, content="""
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
        return render_to_json_response(_("Message sent"))
    return render_to_json_response(respmsg=error, status=500)
