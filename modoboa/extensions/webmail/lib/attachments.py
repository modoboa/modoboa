import os
from rfc6266 import build_header
from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from modoboa.lib import parameters
from modoboa.lib.exceptions import InternalError
from modoboa.lib.webutils import size2integer


def set_compose_session(request):
    """Initialize a new "compose" session.

    It is used to keep track of attachments defined with a new
    message. Each new message will be associated with a unique ID (in
    order to avoid conflicts between users).

    :param request: a Request object.
    :return: the new unique ID.
    """
    import uuid
    randid = str(uuid.uuid4()).replace("-", "")
    request.session["compose_mail"] = {"id": randid, "attachments": []}
    return randid


def save_attachment(f):
    """Save a new attachment to the filesystem.

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.

    :param f: an uploaded file object (see Django's documentation)
    :return: the new random name
    """
    from tempfile import NamedTemporaryFile

    dstdir = os.path.join(settings.MEDIA_ROOT, "webmail")
    try:
        fp = NamedTemporaryFile(dir=dstdir, delete=False)
    except Exception as e:
        raise InternalError(str(e))
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return fp.name


def clean_attachments(attlist):
    """Remove all attachments from the filesystem

    :param attlist: a list of 2-uple. Each element must contain the
                    following information : (random name, real name).
    """
    for att in attlist:
        fullpath = os.path.join(settings.MEDIA_ROOT, "webmail", att["tmpname"])
        try:
            os.remove(fullpath)
        except OSError:
            pass


def create_mail_attachment(attdef, payload=None):
    """Create the MIME part corresponding to the given attachment.

    Mandatory keys: 'fname', 'tmpname', 'content-type'

    :param attdef: a dictionary containing the attachment definition
    :return: a MIMEBase object
    """
    from email import Encoders
    from email.mime.base import MIMEBase

    if "content-type" in attdef:
        maintype, subtype = attdef["content-type"].split("/")
    elif "Content-Type" in attdef:
        maintype, subtype = attdef["Content-Type"].split("/")
    else:
        return None
    res = MIMEBase(maintype, subtype)
    if payload is None:
        with open(os.path.join(
            settings.MEDIA_ROOT, "webmail", attdef["tmpname"]), "rb") as fp:
            res.set_payload(fp.read())
    else:
        res.set_payload(payload)
    Encoders.encode_base64(res)
    if type(attdef['fname']) is str:
        attdef['fname'] = attdef['fname'].decode('utf-8')
    res['Content-Disposition'] = build_header(attdef['fname'])
    return res


class AttachmentUploadHandler(FileUploadHandler):
    """
    Simple upload handler to limit the size of the attachments users
    can upload.
    """

    def __init__(self, request=None):
        super(AttachmentUploadHandler, self).__init__(request)
        self.total_upload = 0
        self.toobig = False
        self.maxsize = size2integer(parameters.get_admin("MAX_ATTACHMENT_SIZE"))

    def receive_data_chunk(self, raw_data, start):
        self.total_upload += len(raw_data)
        if self.total_upload >= self.maxsize:
            self.toobig = True
            raise SkipFile()
        return raw_data

    def file_complete(self, file_size):
        return None
