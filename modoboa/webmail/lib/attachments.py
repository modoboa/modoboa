from email import encoders
from email.mime.base import MIMEBase
import os
import uuid

import six

from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from django.utils.encoding import smart_bytes

from modoboa.lib.exceptions import InternalError
from modoboa.lib.web_utils import size2integer
from modoboa.parameters import tools as param_tools

from .rfc6266 import build_header


def get_storage_path(filename):
    """Return a path to store a file."""
    storage_dir = os.path.join(settings.MEDIA_ROOT, "webmail")
    if not filename:
        return storage_dir
    return os.path.join(storage_dir, filename)


def set_compose_session(request):
    """Initialize a new "compose" session.

    It is used to keep track of attachments defined with a new
    message. Each new message will be associated with a unique ID (in
    order to avoid conflicts between users).

    :param request: a Request object.
    :return: the new unique ID.
    """
    randid = str(uuid.uuid4()).replace("-", "")
    request.session["compose_mail"] = {"id": randid, "attachments": []}
    return randid


def save_attachment(f):
    """Save a new attachment to the filesystem.

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.

    :param f: an uploaded file object (see Django's documentation) or bytes
    :return: the new random name
    """
    from tempfile import NamedTemporaryFile

    try:
        fp = NamedTemporaryFile(dir=get_storage_path(""), delete=False)
    except Exception as e:
        raise InternalError(str(e)) from None
    if isinstance(f, (six.binary_type, six.text_type)):
        fp.write(smart_bytes(f))
    else:
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
        fullpath = get_storage_path(att["tmpname"])
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
    if "content-type" in attdef:
        maintype, subtype = attdef["content-type"].split("/")
    elif "Content-Type" in attdef:
        maintype, subtype = attdef["Content-Type"].split("/")
    else:
        return None
    res = MIMEBase(maintype, subtype)
    if payload is None:
        path = get_storage_path(attdef["tmpname"])
        with open(path, "rb") as fp:
            res.set_payload(fp.read())
    else:
        res.set_payload(payload)
    encoders.encode_base64(res)
    if isinstance(attdef["fname"], six.binary_type):
        attdef["fname"] = attdef["fname"].decode("utf-8")
    content_disposition = build_header(attdef["fname"])
    if isinstance(content_disposition, six.binary_type):
        res["Content-Disposition"] = content_disposition.decode("utf-8")
    else:
        res["Content-Disposition"] = content_disposition
    return res


class AttachmentUploadHandler(FileUploadHandler):
    """
    Simple upload handler to limit the size of the attachments users
    can upload.
    """

    def __init__(self, request=None):
        super().__init__(request)
        self.total_upload = 0
        self.toobig = False
        self.maxsize = size2integer(
            param_tools.get_global_parameter("max_attachment_size")
        )

    def receive_data_chunk(self, raw_data, start):
        self.total_upload += len(raw_data)
        if self.total_upload >= self.maxsize:
            self.toobig = True
            raise SkipFile()
        return raw_data

    def file_complete(self, file_size):
        return None
