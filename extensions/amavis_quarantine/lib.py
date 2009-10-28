import socket
import re
import struct
import string
from django.conf import settings

def getParam(param, default=None):
    try:
        res = getattr(settings, param)
    except AttributeError:
        res = default
    return res

class AMrelease(object):
    def __init__(self):
        mode = getParam('AM_PDP_MODE', "unix")
        if mode == "inet":
            host = getParam('AM_PDP_HOST', 'localhost')
            port = getParam('AM_PDP_PORT', '9998')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, int(port)))
        else:
            path = getParam('AM_PDP_SOCKET', '/var/amavis/amavisd.sock')
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(path)

    def decode(self, answer):
        def repl(match):
            return struct.pack("B", string.atoi(match.group(0)[1:], 16))

        return re.sub(r"%([0-9a-fA-F]{2})", repl, answer)

    def __del__(self):
        self.sock.close()

    def sendreq(self, mailid, secretid, recipient, *others):
        self.sock.send("""request=release
mail_id=%s
secret_id=%s
quar_type=Q
recipient=%s

""" % (mailid, secretid, recipient))
        answer = self.sock.recv(1024)
        answer = self.decode(answer)
        if re.search("250 [\d\.]+ Ok", answer):
            return True
        return False
