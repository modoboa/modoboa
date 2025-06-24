from email import encoders
from email.mime.base import MIMEBase
import json
import os
from tempfile import NamedTemporaryFile
import uuid

import six

from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from django.http import Http404
from django.utils.encoding import smart_bytes
from django.utils.translation import gettext as _

from modoboa.lib.exceptions import InternalError
from modoboa.lib.redis import get_redis_connection
from modoboa.lib.web_utils import size2integer
from modoboa.parameters import tools as param_tools

from .rfc6266 import build_header


class ComposeSessionManager:

    def __init__(self, username: str):
        self.hash = f"webmail-{username}"
        self.rclient = get_redis_connection(bytes)

    def create(self) -> str:
        """
        Initialize a new "compose" session.

        It is used to keep track of attachments defined with a new
        message. Each new message will be associated with a unique ID (in
        order to avoid conflicts between users).
        """
        randid = str(uuid.uuid4()).replace("-", "")
        self.rclient.hset(self.hash, randid, json.dumps({"attachments": []}))
        return randid

    def delete(self, uid: str) -> None:
        self.rclient.hdel(self.hash, uid)

    def exists(self, uid: str) -> bool:
        return self.rclient.hexists(self.hash, uid)

    def get_content(self, uid: str) -> dict:
        if not self.exists(uid):
            raise Http404
        content = self.rclient.hget(self.hash, uid)
        return json.loads(content.decode())

    def set_content(self, uid: str, content: dict):
        return self.rclient.hset(self.hash, uid, json.dumps(content))


def get_storage_path(filename):
    """Return a path to store a file."""
    storage_dir = os.path.join(settings.MEDIA_ROOT, "webmail")
    if not filename:
        return storage_dir
    return os.path.join(storage_dir, filename)


def save_attachment(request, session_uid: str, f) -> dict:
    """Save a new attachment to the filesystem.

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.

    :param f: an uploaded file object (see Django's documentation) or bytes
    :return: the new random name
    """
    manager = ComposeSessionManager(request.user.username)
    if not manager.exists(session_uid):
        raise Http404
    try:
        fp = NamedTemporaryFile(dir=get_storage_path(""), delete=False)
    except Exception as e:
        raise InternalError(str(e)) from None
    if isinstance(f, six.binary_type | six.text_type):
        fp.write(smart_bytes(f))
    else:
        for chunk in f.chunks():
            fp.write(chunk)
    fp.close()

    session = manager.get_content(session_uid)
    attachment = {
        "fname": str(f),
        "content-type": f.content_type,
        "size": f.size,
        "tmpname": os.path.basename(fp.name),
    }
    session["attachments"].append(attachment)
    manager.set_content(session_uid, session)
    return attachment


def remove_attachment(request, session_uid: str, name: str) -> str | None:
    manager = ComposeSessionManager(request.user.username)
    session = manager.get_content(session_uid)
    for att in session["attachments"]:
        if att["tmpname"] == name:
            session["attachments"].remove(att)
            fullpath = os.path.join(settings.MEDIA_ROOT, "webmail", att["tmpname"])
            try:
                os.remove(fullpath)
            except OSError as e:
                return _("Failed to remove attachment: ") + str(e)
            manager.set_content(session_uid, session)
            return None
    raise Http404


def remove_attachments_and_session(
    manager: ComposeSessionManager, session_uid: str
) -> None:
    content = manager.get_content(session_uid)
    for att in content["attachments"]:
        fullpath = get_storage_path(att["tmpname"])
        try:
            os.remove(fullpath)
        except OSError:
            pass
    manager.delete(session_uid)


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
