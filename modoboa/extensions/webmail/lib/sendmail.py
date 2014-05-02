import smtplib
from modoboa.lib import parameters
from modoboa.lib.emailutils import prepare_addresses
from modoboa.lib.webutils import _render_to_string
from modoboa.lib.cryptutils import get_password
from modoboa.extensions.webmail.exceptions import WebmailInternalError
from . import get_imapconnector, clean_attachments


def send_mail(request, form, posturl=None):
    """Email verification and sending.

    If the form does not present any error, a new MIME message is
    constructed. Then, a connection is established with the defined
    SMTP server and the message is finally sent.

    :param request: a Request object
    :param posturl: the url to post the message form to
    :return: a 2-uple (True|False, HttpResponse)
    """
    if not form.is_valid():
        editormode = parameters.get_user(request.user, "EDITOR")
        listing = _render_to_string(
            request, "webmail/compose.html",
            {"form": form, "noerrors": True,
             "body": form.cleaned_data.get("body", "").strip(),
             "posturl": posturl}
        )
        return False, dict(status="ko", listing=listing, editor=editormode)

    msg = form.to_msg(request)
    rcpts = prepare_addresses(form.cleaned_data["to"], "envelope")
    for hdr in ["cc", "cci"]:
        if form.cleaned_data[hdr]:
            msg[hdr.capitalize()] = prepare_addresses(form.cleaned_data[hdr])
            rcpts += prepare_addresses(form.cleaned_data[hdr], "envelope")
    try:
        secmode = parameters.get_admin("SMTP_SECURED_MODE")
        if secmode == "ssl":
            s = smtplib.SMTP_SSL(parameters.get_admin("SMTP_SERVER"),
                                 int(parameters.get_admin("SMTP_PORT")))
        else:
            s = smtplib.SMTP(parameters.get_admin("SMTP_SERVER"),
                             int(parameters.get_admin("SMTP_PORT")))
            if secmode == "starttls":
                s.starttls()
    except Exception as text:
        raise WebmailInternalError(str(text))

    if parameters.get_admin("SMTP_AUTHENTICATION") == "yes":
        try:
            s.login(request.user.username, get_password(request))
        except smtplib.SMTPException as err:
            raise WebmailInternalError(str(err))
    try:
        s.sendmail(request.user.email, rcpts, msg.as_string())
        s.quit()
    except smtplib.SMTPException as err:
        raise WebmailInternalError(str(err))

    sentfolder = parameters.get_user(request.user, "SENT_FOLDER")
    get_imapconnector(request).push_mail(sentfolder, msg)
    clean_attachments(request.session["compose_mail"]["attachments"])
    del request.session["compose_mail"]
    return True, {}
