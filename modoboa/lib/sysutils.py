# coding: utf-8

"""
This module extra functions/shortcuts to communicate with the system
(executing commands, etc.)
"""
import logging
import logging.handlers
from modoboa.lib import parameters

def exec_cmd(cmd, sudo_user=None, **kwargs):
    import subprocess

    if sudo_user is not None:
        cmd = "sudo -u %s %s" % (sudo_user, cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                         stderr=subprocess.STDOUT, **kwargs)
    output = p.communicate()[0]
    return p.returncode, output

def exec_as_vuser(cmd):
    code, output = exec_cmd("sudo -u %s %s" \
                                % (parameters.get_admin("MAILBOXES_OWNER", app="admin"), cmd))
    if code:
        exec_cmd("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True

def __log(msg, facility=logging.handlers.SysLogHandler.LOG_AUTH):
    logger = logging.getLogger('modoboa')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address='/dev/log', facility=facility)
    formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def log_warning(msg):
    logger = __log(msg)
    logger.warning(msg)
