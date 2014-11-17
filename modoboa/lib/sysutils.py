# coding: utf-8

"""
This module extra functions/shortcuts to communicate with the system
(executing commands, etc.)
"""
import subprocess
import inspect
import re


def exec_cmd(cmd, sudo_user=None, pinput=None, capture_output=True, **kwargs):
    """Execute a shell command.

    Run a command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.

    :param str cmd: the command to execute
    :param str sudo_user: a valid system username
    :param str pinput: data to send to process's stdin
    :param bool capture_output: capture process output or not
    :rtype: tuple
    :return: return code, command output
    """
    if sudo_user is not None:
        cmd = "sudo -u %s %s" % (sudo_user, cmd)
    kwargs["shell"] = True
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


def guess_extension_name():
    """Tries to guess the application's name by inspecting the stack.

    :return: a string or None
    """
    modname = inspect.getmodule(inspect.stack()[2][0]).__name__
    match = re.match(r"(?:modoboa\.)?(?:extensions\.)?([^\.$]+)", modname)
    if match is not None:
        return match.group(1)
    return None
