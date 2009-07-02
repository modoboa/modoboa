#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import sys
import re
import struct
from optparse import OptionParser

def getsocket(options):
    if options.mode == "net":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((options.host, options.port))

    return s

def from_stdin():
    res = []
    for line in sys.stdin:
        res += [line]
    return res

def decodevalue(val):
    def pack(match):
        return struct.pack('B', match.group(0))
    res = re.sub("%([0-9a-fA-F]{2})", pack, val)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-o", "--host", default="127.0.0.1",
                      help="")
    parser.add_option("-p", "--port", default=9998,
                      help="")
    parser.add_option("-s", "--socket", default="",
                      help="")
    parser.add_option("-m", "--mode", default="unix",
                      help="")
    (options, args) = parser.parse_args()
    
    if not len(args):
        print "Nothing to do, exiting."
        sys.exit(1)

    s = getsocket(options)
#     if args[0] == '-':
#         worklist = from_stdin()
#     else:
#         worklist = [args[0]]

#    for message in worklist:
#        params = message.split()
    params = ["k1URJIk76bKa", "k1URJIk76bKa", "antoine.nguyen@streamcore.com"]
    cmd = """request=release
mail_id=%s
secret_id=%s
quar_type=Q
recipient=%s

""" % (params[0], params[1], params[2])
    s.send(cmd)
    answer = s.recv(1024)
    print answer
    
    s.close()
