"""Value loading functions."""

from typing import List, Optional, TypedDict

from modoboa.webmail.lib import imaputils


class UserMailbox(TypedDict):
    """Type definition for user mailbox."""

    name: str
    label: str


def __build_folders_list(
    folders: list, user, imapc: imaputils.IMAPconnector, parentmb: Optional[str] = None
) -> List[UserMailbox]:
    ret: List[UserMailbox] = []
    for fd in folders:
        value = fd["path"] if "path" in fd else fd["name"]
        if parentmb:
            ret += [
                {
                    "name": value,
                    "label": fd["name"].replace(f"{parentmb}{imapc.hdelimiter}", ""),
                }
            ]
        else:
            ret += [{"name": value, "label": fd["name"]}]
        if "sub" in fd:
            submboxes = imapc.getmboxes(user, value)
            ret += __build_folders_list(submboxes, user, imapc, value)
    return ret


def user_mailboxes(request) -> List[UserMailbox]:
    """Retrieve list of available mailboxes for given user."""
    mbc = imaputils.get_imapconnector(request, load_namespaces=False)
    ret = mbc.getmboxes(request.user)
    folders = __build_folders_list(ret, request.user, mbc)
    return folders
