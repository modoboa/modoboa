# coding: utf-8

"""
This module extra functions/shortcuts to communicate with the system
(executing commands, etc.)
"""
import subprocess


def exec_cmd(cmd, sudo_user=None, **kwargs):
    """Execute a shell command.

    Run a command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.

    :param str cmd: the command to execute
    :param str sudo_user: a valid system username
    :rtype: tuple
    :return: return code, command output
    """
    if sudo_user is not None:
        cmd = "sudo -u %s %s" % (sudo_user, cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, **kwargs)
    output = p.communicate()[0]
    return p.returncode, output
