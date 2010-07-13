import socket
import re
import struct
import string
from modoboa.lib import parameters

class AMrelease(object):
    def __init__(self):
        mode = parameters.get_admin("amavis_quarantine", "AM_PDP_MODE")
        if mode == "inet":
            host = parameters.get_admin("amavis_quarantine", 'AM_PDP_HOST')
            port = parameters.get_admin("amavis_quarantine", 'AM_PDP_PORT')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, int(port)))
        else:
            path = parameters.get_admin("amavis_quarantine", 'AM_PDP_SOCKET')
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
