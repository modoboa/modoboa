"""The code used to generate PDF files (based on Reportlab)."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import utils
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Frame,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from django.utils.translation import gettext as _

from modoboa.parameters import tools as param_tools

from . import lib

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Footer",
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
        textColor=colors.lightgrey,
    )
)
styles.add(
    ParagraphStyle(
        name="Warning", fontName="Helvetica-Oblique", textColor=colors.red, fontSize=12
    )
)
styles.add(ParagraphStyle(name="Link", textColor=colors.blue))
styles.add(
    ParagraphStyle(
        name="Greeting", alignment=TA_CENTER, fontName="Helvetica-Oblique", fontSize=14
    )
)


def resized_image(path, width=1 * cm):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))


def credentials(account, password):
    """Generate a PDF document containing account credentials."""

    def page_template(canvas, doc):
        canvas.setTitle(_("Personal account information"))
        canvas.setAuthor(account.fullname)
        canvas.setCreator("Modoboa")
        footer = [
            Paragraph(
                _("Powered by Modoboa - Mail hosting made simple"), styles["Footer"]
            )
        ]
        Frame(0, 0, 21 * cm, 2 * cm).addFromList(footer, canvas)

    conf = dict(param_tools.get_global_parameters("pdfcredentials"))
    filename = lib.get_creds_filename(account)
    buff = BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=A4)
    story = []
    logo = lib.get_document_logo()
    if logo is not None:
        story.append(resized_image(logo, 8 * cm))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(conf["title"], styles["Title"]))
    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            _(
                """
Dear %s, this document contains the credentials you will need
to connect to Modoboa. Learn the content and destroy
the document as soon as possible.
"""
            )
            % account.fullname,
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(_("Web panel:"), styles["h3"]))
    data = [
        ["URL", conf["webpanel_url"]],
        [_("Username"), account.username],
        [_("Password"), password],
    ]
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("TEXTCOLOR", (1, 0), (1, 0), colors.blue),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            _(
                """
Here you can view your emails anytime online, create filters or manage
your contacts.
"""
            ),
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(_("Please change your password!"), styles["Warning"]))

    if conf["include_connection_settings"]:
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(_("PC/Tablet/Smartphone configuration:"), styles["h3"]))
        story.append(Spacer(1, 0.2 * cm))
        data = [
            [_("SMTP server address"), conf["smtp_server_address"]],
            [_("SMTP server port"), conf["smtp_server_port"]],
            [_("SMTP connection security"), conf["smtp_connection_security"]],
            [_("IMAP server address"), conf["imap_server_address"]],
            [_("IMAP server port"), conf["imap_server_port"]],
            [_("IMAP connection security"), conf["imap_connection_security"]],
        ]
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                _("Use those settings for your computer, tablet or phone."),
                styles["Normal"],
            )
        )

    if conf["custom_message"]:
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(conf["custom_message"], styles["Greeting"]))

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    length = len(buff.getvalue())
    buff.seek(0)
    lib.crypt_and_save_to_file(buff, filename, length)
