from datetime import timedelta
from email import encoders
from email.mime.base import MIMEBase
import json
import os
from tempfile import NamedTemporaryFile
import time
from typing import TypedDict
import uuid


from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from django.http import Http404
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _

from modoboa.lib.exceptions import InternalError
from modoboa.lib.redis import get_redis_connection
from modoboa.lib.web_utils import size2integer
from modoboa.parameters import tools as param_tools

from .rfc6266 import build_header

Attachment = TypedDict(
    "Attachment", {"fname": str, "content-type": str, "size": int, "tmpname": str}
)

# Compose sessions expire after this delay without activity
COMPOSE_SESSION_TTL = timedelta(days=1)
# Files younger than this are never considered orphans (upload in progress)
ORPHAN_GRACE_PERIOD = timedelta(hours=1)

COMPOSE_SESSION_KEY_PREFIX = "webmail:compose"


class ComposeSessionManager:
    """Compose sessions, stored in Redis with an expiration delay.

    A session keeps track of the attachments uploaded for a message being
    written. Each session has its own key so that abandoned sessions
    expire instead of piling up.
    """

    def __init__(self, username: str):
        self.username = username
        self.rclient = get_redis_connection(bytes)

    def _key(self, uid: str) -> str:
        return f"{COMPOSE_SESSION_KEY_PREFIX}:{self.username}:{uid}"

    def create(self) -> str:
        """
        Initialize a new "compose" session.

        Each new message will be associated with a unique ID (in order to
        avoid conflicts between users).
        """
        randid = uuid.uuid4().hex
        self.set_content(randid, {"attachments": []})
        return randid

    def delete(self, uid: str) -> None:
        self.rclient.delete(self._key(uid))

    def exists(self, uid: str) -> bool:
        return bool(self.rclient.exists(self._key(uid)))

    def get_content(self, uid: str) -> dict:
        content = self.rclient.get(self._key(uid))
        if content is None:
            raise Http404
        # Keep a session in use alive
        self.rclient.expire(self._key(uid), COMPOSE_SESSION_TTL)
        return json.loads(content.decode())

    def set_content(self, uid: str, content: dict):
        return self.rclient.set(
            self._key(uid), json.dumps(content), ex=COMPOSE_SESSION_TTL
        )


def get_attachments_dir() -> str:
    """Return the directory holding webmail attachments.

    It contains the files of messages being written and the attachments
    of scheduled messages: it must never be served by the web server, so
    it defaults to a directory next to MEDIA_ROOT, not inside it.
    """
    return getattr(settings, "WEBMAIL_ATTACHMENTS_ROOT", None) or os.path.join(
        settings.BASE_DIR, "webmail_attachments"
    )


def get_storage_path(filename):
    """Return the path of an attachment file.

    Only the file name is kept: a stored name can never point outside
    the attachments directory.
    """
    storage_dir = get_attachments_dir()
    if not filename:
        return storage_dir
    return os.path.join(storage_dir, os.path.basename(filename))


@deconstructible(path="modoboa.webmail.lib.attachments.WebmailAttachmentStorage")
class WebmailAttachmentStorage(FileSystemStorage):
    """Private storage for webmail attachments: files have no URL."""

    @property
    def base_location(self):
        return get_attachments_dir()

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None


def _create_attachment_file():
    """Create a new file with a random name in the attachments directory."""
    storage_dir = get_attachments_dir()
    try:
        os.makedirs(storage_dir, mode=0o700, exist_ok=True)
        return NamedTemporaryFile(dir=storage_dir, delete=False)
    except OSError as e:
        raise InternalError(str(e)) from None


def save_attachment_from_upload(request, session_uid: str, f) -> Attachment:
    """
    Save a new attachment to the filesystem, directly from a Django upload.

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.

    :param f: an uploaded file object (see Django's documentation)
    """
    manager = ComposeSessionManager(request.user.username)
    if not manager.exists(session_uid):
        raise Http404
    fp = _create_attachment_file()
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()

    session = manager.get_content(session_uid)
    attachment: Attachment = {
        "fname": str(f),
        "content-type": f.content_type,
        "size": f.size,
        "tmpname": os.path.basename(fp.name),
    }
    session["attachments"].append(attachment)
    manager.set_content(session_uid, session)
    return attachment


def save_attachment(
    request, session_uid: str, filename: str, content_type: str, content: str | bytes
) -> Attachment:
    """
    Save a new attachment to the filesystem

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.
    """
    manager = ComposeSessionManager(request.user.username)
    if not manager.exists(session_uid):
        raise Http404
    fp = _create_attachment_file()
    if isinstance(content, str):
        content = content.encode("utf-8")
    fp.write(content)
    fp.close()

    session = manager.get_content(session_uid)
    attachment: Attachment = {
        "fname": filename,
        "content-type": content_type,
        "size": len(content),
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
            fullpath = get_storage_path(att["tmpname"])
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


def cleanup_orphan_attachments() -> int:
    """Delete attachment files no longer used by anything.

    A file is kept while a compose session or a scheduled message refers
    to it. Others come from abandoned or expired sessions and are removed,
    except very recent ones (the session may not reference them yet).

    :return: the number of removed files
    """
    from modoboa.webmail.models import MessageAttachment

    storage_dir = get_attachments_dir()
    if not os.path.isdir(storage_dir):
        return 0
    used = {
        os.path.basename(name)
        for name in MessageAttachment.objects.values_list("file", flat=True)
    }
    rclient = get_redis_connection(bytes)
    for key in rclient.scan_iter(match=f"{COMPOSE_SESSION_KEY_PREFIX}:*"):
        content = rclient.get(key)
        if content is None:
            continue
        for att in json.loads(content.decode()).get("attachments", []):
            used.add(att["tmpname"])
    limit = time.time() - ORPHAN_GRACE_PERIOD.total_seconds()
    removed = 0
    for entry in os.scandir(storage_dir):
        if not entry.is_file() or entry.name in used:
            continue
        if entry.stat().st_mtime > limit:
            continue
        try:
            os.remove(entry.path)
        except OSError:
            continue
        removed += 1
    return removed


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
    if isinstance(attdef["fname"], bytes):
        attdef["fname"] = attdef["fname"].decode("utf-8")
    content_disposition = build_header(attdef["fname"])
    if isinstance(content_disposition, bytes):
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
