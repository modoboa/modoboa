# coding: utf-8

"""
This module extra functions/shortcuts to communicate with the system
(executing commands, etc.)
"""

from modoboa.lib import parameters

def exec_cmd(cmd, **kwargs):
    import subprocess

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, **kwargs)
    output = p.communicate()[0]
    return p.returncode, output

def exec_as_vuser(cmd):
    code, output = exec_cmd("sudo -u %s %s" \
                                % (parameters.get_admin("VIRTUAL_UID", app="admin"), cmd))
    if code:
        exec_cmd("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True
