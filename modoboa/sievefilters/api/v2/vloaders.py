"""Value loading functions."""

from typing import TypedDict

from modoboa.webmail.lib import imaputils


class UserMailbox(TypedDict):
    """Type definition for user mailbox."""

    name: str
    label: str


def __build_folders_list(
    folders: list, user, imapc: imaputils.IMAPconnector, parentmb: str | None = None
) -> list[UserMailbox]:
    ret: list[UserMailbox] = []
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
            submboxes = imapc.getmboxes(user, value, unseen_messages=False)
            ret += __build_folders_list(submboxes, user, imapc, value)
    return ret


def user_mailboxes(request) -> list[UserMailbox]:
    """Retrieve list of available mailboxes for given user."""
    with imaputils.get_imapconnector(request) as mbc:
        # Unseen counters are useless here and cost a STATUS per mailbox
        ret = mbc.getmboxes(request.user, unseen_messages=False)
        folders = __build_folders_list(ret, request.user, mbc)
    return folders
