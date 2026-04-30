"""
This module extra functions/shortcuts to communicate with the system
(executing commands, etc.)
"""

import inspect
import os
import pwd
import re
import subprocess

from django.conf import settings
from django.utils.encoding import force_str


def exec_cmd(cmd, sudo_user=None, pinput=None, capture_output=True, **kwargs):
    """Execute a shell command.

    Run a command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.

    Backport of CVE-2026-27602: callers must now pass ``shell=True``
    explicitly when ``cmd`` is a shell string. Prefer passing ``cmd``
    as a ``list[str]`` (with ``shell`` left unset/False) so arguments
    are not subject to shell interpretation.

    :param cmd: the command to execute (``str`` with ``shell=True``,
        or ``list[str]``)
    :param str sudo_user: a valid system username
    :param str pinput: data to send to process's stdin
    :param bool capture_output: capture process output or not
    :rtype: tuple
    :return: return code, command output
    """
    if sudo_user is not None:
        if isinstance(cmd, list):
            cmd = ["sudo", "-u", sudo_user] + cmd
        else:
            cmd = "sudo -u %s %s" % (sudo_user, cmd)
    if pinput is not None:
        kwargs["stdin"] = subprocess.PIPE
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process = subprocess.Popen(cmd, **kwargs)
    if pinput or capture_output:
        c_args = [pinput] if pinput is not None else []
        output = process.communicate(*c_args)[0]
    else:
        output = None
        process.wait()
    return process.returncode, output


def doveadm_cmd(params, pinput=None, capture_output=True, **kwargs):
    """Execute doveadm command.

    Run doveadm command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.

    Backport of CVE-2026-27602: ``params`` must be a ``list[str]`` so the
    arguments are passed to ``subprocess`` without shell interpretation.

    :param list params: the parameters to give to doveadm
    :param str sudo_user: a valid system username
    :param str pinput: data to send to process's stdin
    :param bool capture_output: capture process output or not
    :rtype: tuple
    :return: return code, command output
    """
    dpath = None
    code, output = exec_cmd("which doveadm", shell=True)
    if not code:
        dpath = force_str(output).strip()
    else:
        known_paths = getattr(
            settings,
            "DOVEADM_LOOKUP_PATH",
            ("/usr/bin/doveadm", "/usr/local/bin/doveadm"),
        )
        for fpath in known_paths:
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                dpath = fpath
                break
    dovecot_user = getattr(settings, "DOVECOT_USER", "vmail")
    curuser = pwd.getpwuid(os.getuid()).pw_name
    sudo_user = dovecot_user if curuser != dovecot_user else None
    if dpath:
        return exec_cmd(
            [dpath] + list(params),
            sudo_user=sudo_user,
            pinput=pinput,
            capture_output=capture_output,
            **kwargs,
        )

    raise OSError("doveadm command not found")


def guess_extension_name():
    """Tries to guess the application's name by inspecting the stack.

    :return: a string or None
    """
    modname = inspect.getmodule(inspect.stack()[2][0]).__name__
    match = re.match(r"(?:modoboa\.)?(?:extensions\.)?([^\.$]+)", modname)
    if match is not None:
        return match.group(1)
    return None
