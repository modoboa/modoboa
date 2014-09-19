# coding: utf-8
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import lxml.html

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from modoboa.lib import parameters
from modoboa.lib.emailutils import set_email_headers
from .lib import (
    ImapEmail, create_mail_attachment
)


def html2plaintext(content):
    """HTML to plain text translation.

    :param content: some HTML content
    """
    if not content:
        return ""
    html = lxml.html.fromstring(content)
    plaintext = ""
    for ch in html.iter():
        p = None
        if ch.text is not None:
            p = ch.text.strip('\r\t\n')
        if ch.tag == "img":
            p = ch.get("alt")
        if p is None:
            continue
        plaintext += p + "\n"
    return plaintext


def make_body_images_inline(body):
    """Looks for images inside the body and make them inline.

    Before sending a message in HTML format, it is necessary to find
    all img tags contained in the body in order to rewrite them. For
    example, icons provided by CKeditor are stored on the server
    filesystem and not accessible from the outside. We must embark
    them as parts of the MIME message if we want recipients to
    display them correctly.

    :param body: the HTML body to parse
    """
    import os
    from email.mime.image import MIMEImage
    from urlparse import urlparse

    html = lxml.html.fromstring(body)
    parts = []
    for tag in html.iter("img"):
        src = tag.get("src")
        if src is None:
            continue
        o = urlparse(src)
        path = os.path.join(settings.MODOBOA_DIR, o.path[1:])
        if not os.path.exists(path):
            continue
        fname = os.path.basename(path)
        cid = "%s@modoboa" % os.path.splitext(fname)[0]
        tag.set("src", "cid:%s" % cid)
        with open(path, "rb") as fp:
            part = MIMEImage(fp.read())
        part["Content-ID"] = "<%s>" % cid
        part.replace_header(
            "Content-Type", '%s; name="%s"' % (part["Content-Type"], fname)
        )
        part["Content-Disposition"] = "inline"
        parts.append(part)
    return lxml.html.tostring(html), parts


class ComposeMailForm(forms.Form):

    """Compose mail form."""

    to = forms.CharField(label=_("To"))
    cc = forms.CharField(label=_("Cc"), required=False)
    cci = forms.CharField(label=_("Cci"), required=False)
    subject = forms.CharField(
        label=_("Subject"),
        max_length=255,
        required=False
    )
    origmsgid = forms.CharField(label="", required=False)
    body = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        """Custom constructor."""
        super(ComposeMailForm, self).__init__(*args, **kwargs)
        self.field_widths = {
            "cc": "11",
            "cci": "11",
            "subject": "11"
        }

    def _html_msg(self):
        """Create a multipart message.

        We attach two alternatives:
        * text/html
        * text/plain
        """
        msg = MIMEMultipart(_subtype="related")
        submsg = MIMEMultipart(_subtype="alternative")
        body = self.cleaned_data["body"]
        charset = "utf-8"
        if body:
            tbody = html2plaintext(body)
            body, images = make_body_images_inline(body)
        else:
            tbody = ""
            images = []
        submsg.attach(
            MIMEText(tbody.encode(charset), _subtype="plain", _charset=charset)
        )
        submsg.attach(
            MIMEText(body.encode(charset), _subtype="html", _charset=charset)
        )
        msg.attach(submsg)
        for img in images:
            msg.attach(img)
        return msg

    def _plain_msg(self):
        """Create a simple text message.
        """
        charset = "utf-8"
        text = MIMEText(self.cleaned_data["body"].encode(charset),
                        _subtype="plain", _charset=charset)
        return text

    def _build_msg(self, request):
        """Convert form's content to a MIME message.
        """
        editormode = parameters.get_user(request.user, "EDITOR")
        msg = getattr(self, "_%s_msg" % editormode)()

        if request.session["compose_mail"]["attachments"]:
            wrapper = MIMEMultipart(_subtype="mixed")
            wrapper.attach(msg)
            for attdef in request.session["compose_mail"]["attachments"]:
                wrapper.attach(create_mail_attachment(attdef))
            msg = wrapper
        return msg

    def to_msg(self, request):
        """Convert form's content to an object ready to send.

        We set headers at the end to be sure no one will override
        them.

        """
        msg = self._build_msg(request)
        set_email_headers(
            msg, self.cleaned_data["subject"], request.user.encoded_address,
            self.cleaned_data['to']
        )
        origmsgid = self.cleaned_data.get("origmsgid", None)
        if origmsgid:
            msg["References"] = msg["In-Reply-To"] = origmsgid
        return msg


class ForwardMailForm(ComposeMailForm):
    """Forward mail form.
    """

    def _build_msg(self, request):
        """Convert form's content to a MIME message.

        We also add original attachments (if any) to the new message.
        """
        from modoboa.extensions.webmail.lib import decode_payload

        mbox = request.GET.get("mbox", None)
        mailid = request.GET.get("mailid", None)
        msg = super(ForwardMailForm, self)._build_msg(request)
        origmsg = ImapEmail(request, False, "%s:%s" % (mbox, mailid))
        if origmsg.attachments:
            if not msg.is_multipart or not msg.get_content_subtype() == "mixed":
                wrapper = MIMEMultipart(_subtype="mixed")
                wrapper.attach(msg)
                msg = wrapper
            for attpart, fname in origmsg.attachments.items():
                attdef, payload = origmsg.fetch_attachment(attpart)
                attdef["fname"] = fname
                msg.attach(create_mail_attachment(
                    attdef, decode_payload(attdef["encoding"], payload)
                ))
        return msg


class FolderForm(forms.Form):
    oldname = forms.CharField(
        label="",
        widget=forms.HiddenInput(attrs={"class": "form-control"}),
        required=False
    )
    name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))


class AttachmentForm(forms.Form):
    attachment = forms.FileField(label=_("Select a file"))
