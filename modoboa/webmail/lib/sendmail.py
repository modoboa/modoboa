import smtplib

from django.core import mail
from django.template.loader import render_to_string

from modoboa.lib.cryptutils import get_password
from modoboa.parameters import tools as param_tools

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
        editormode = request.user.parameters.get_value("editor")
        listing = render_to_string(
            "modoboa_webmail/compose.html",
            {
                "form": form,
                "noerrors": True,
                "body": form.cleaned_data.get("body", "").strip(),
                "posturl": posturl,
            },
            request,
        )
        return False, {"status": "ko", "listing": listing, "editor": editormode}

    msg = form.to_msg(request)
    conf = dict(param_tools.get_global_parameters("modoboa_webmail"))
    options = {"host": conf["smtp_server"], "port": conf["smtp_port"]}
    if conf["smtp_secured_mode"] == "ssl":
        options.update({"use_ssl": True})
    elif conf["smtp_secured_mode"] == "starttls":
        options.update({"use_tls": True})
    if conf["smtp_authentication"]:
        options.update(
            {"username": request.user.username, "password": get_password(request)}
        )
    try:
        with mail.get_connection(**options) as connection:
            msg.connection = connection
            msg.send()
    except smtplib.SMTPResponseException as inst:
        return False, {"status": "ko", "error": inst.smtp_error}
    except smtplib.SMTPRecipientsRefused as inst:
        error = ", ".join(
            [f"{rcpt}: {error}" for rcpt, error in inst.recipients.items()]
        )
        return False, {"status": "ko", "error": error}

    # Copy message to sent folder
    sentfolder = request.user.parameters.get_value("sent_folder")
    get_imapconnector(request).push_mail(sentfolder, msg.message())
    clean_attachments(request.session["compose_mail"]["attachments"])
    del request.session["compose_mail"]

    return True, {}
