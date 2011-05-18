#!/usr/bin/env python
# coding: utf-8

"""MANAGESIEVE client.

A protocol for securely managing Sieve scripts on a remote server.
This protocol allows a user to have multiple scripts, and also alerts
a user to syntactically flawed scripts.

Implementation based on <draft-martin-managesieve-12>.
"""

import sys, os
import socket
import re
import base64
import ssl

from digest_md5 import DigestMD5

CRLF = '\r\n'

KNOWN_CAPABILITIES = ["IMPLEMENTATION", "SASL", "SIEVE", 
                      "STARTTLS", "NOTIFY", "LANGUAGE",
                      "RENAME", "NOOP", "UNAUTHENTICATE"]

SUPPORTED_AUTH_MECHS = ["DIGEST-MD5", "PLAIN", "LOGIN"]

class Error(Exception):
    pass

class Response(Exception):
    def __init__(self, code, data):
        self.code = code
        self.data = data

    def __str__(self):
        return "%s %s" % (self.code, self.data)

def authentication_required(meth):
    """Simple class method decorator.

    Checks if the client is currently connected.

    :param meth: the original called method
    """
    def check(cls, *args, **kwargs):
        if cls.authenticated:
            return meth(cls, *args, **kwargs)
        raise Error("Authentication required")
    return check

class ManageSieveClient:
    read_size = 4096
    read_timeout = 5

    def __init__(self, srvaddr, srvport=2000, debug=False):
        self.srvaddr = srvaddr
        self.srvport = srvport
        self.__debug = debug
        self.sock = None
        self.__read_buffer = ""
        self.authenticated = False
        self.errcode = None

        self.__capabilities = {}
        self.__respcode_expr = re.compile("(OK|NO|BYE)\s*(.+)?")
        self.__error_expr = re.compile('(\(\w+\))?\s*(".+")')
        self.__size_expr = re.compile("\{(\d+)\+?\}")
        self.__active_expr = re.compile("ACTIVE", re.IGNORECASE)

    def __del__(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def __dprint(self, message):
        if not self.__debug:
            return
        print "DEBUG: %s" % message

    def __read_block(self, size):
        """Read a block of 'size' bytes from the server.

        An internal buffer is used to read data from the server. If
        enough data is available from it, we return that data.

        Eventually, we try to grab the missing part from the server
        for ManageSieveClient.read_timeout seconds. If no data can be
        retrieved, it is considered as a fatal error and an 'Error'
        exception is raised.

        :param size: number of bytes to read
        :rtype: string
        :returns: the read block (can be empty)
        """
        buf = ""
        if len(self.__read_buffer):
            limit = size if size <= len(self.__read_buffer) else len(self.__read_buffer)
            buf = self.__read_buffer[:limit]
            self.__read_buffer = self.__read_buffer[limit:]
            size -= limit
        if not size:
            return buf
        try:
            buf += self.sock.recv(size)
        except (socket.timeout, ssl.SSLError), e:
            raise Error("Failed to read %d bytes from the server" % size)
        return buf

    def __read_line(self):
        """Read one line from the server.

        An internal buffer is used to read data from the server
        (blocks of ManageSieveClient.read_size bytes). If the buffer
        is not empty, we try to find an entire line to return.

        If we failed, we try to read new content from the server for
        ManageSieveClient.read_timeout seconds. If no data can be
        retrieved, it is considered as a fatal error and an 'Error'
        exception is raised.
        
        :rtype: string
        :return: the read line
        """
        ret = ""
        while True:
            try:
                pos = self.__read_buffer.index(CRLF)
                ret = self.__read_buffer[0:pos]
                self.__read_buffer = self.__read_buffer[pos+len(CRLF):]
                break
            except ValueError:
                pass
            try:
                nval = self.sock.recv(self.read_size)
                if not len(nval):
                    break
                self.__read_buffer += nval
            except (socket.timeout, ssl.SSLError):
                raise Error("Failed to read data from the server")
        if len(ret):
            m = self.__respcode_expr.match(ret)
            if m:
                if m.group(1) == "BYE":
                    raise Error("Connection closed by server")
                if m.group(1) == "NO":
                    self.__parse_error(m.group(2))
                raise Response(m.group(1), m.group(2))
        return ret

    def __read_response(self, nblines=-1):
        """Read a response from the server.

        In the usual case, we read lines until we find one that looks
        like a response (OK|NO|BYE\s*(.+)?).

        If *nblines* > 0, we read excactly nblines before returning.

        :param nblines: number of lines to read (default : -1)
        :rtype: tuple
        :return: a tuple of the form (code, data, response). If
        nblines is provided, code and data can be equal to None.
        """
        resp, code, data = ("", None, None)
        cpt = 0
        while True:
            try:
                line = self.__read_line()
            except Response, inst:
                code = inst.code
                data = inst.data
                break                
            if not len(line):
                break
            resp += line + CRLF
            cpt += 1
            if nblines != -1 and cpt == nblines:
                break

        return (code, data, resp)
    
    def __prepare_args(self, args):
        """Format command arguments before sending them.

        Command arguments of type string must be quoted, the only
        exception concerns size indication (of the form {\d\+?}).

        :param args: list of arguments
        :return: a list for transformed arguments
        """
        ret = []
        for a in args:
            if type(a) in [str, unicode] and self.__size_expr.match(a) is None:
                ret += ['"%s"' % a]
                continue
            ret += ["%s" % str(a)]
        return ret

    def __send_command(self, name, args=[], withcontent=False, extralines=[], nblines=-1):
        """Send a command to the server.

        If args is not empty, we concatenate the given command with
        the content of this list. If extralines is not empty, they are
        sent one by one to the server. (CLRF are automatically appended to them)

        We wait for a response just after the command has been sent.

        :param name: the command to sent
        :param args: a list of arguments for this command
        :param withcontent: tells the function to return the server's response or not
        :param extralines: a list of extra lines to sent after the command
        :param nblines: the number of response lines to read (all by default)

        :returns: a tuple of the form (code, data[, response])
        """
        tosend = name
        if len(args):
            tosend += " " + " ".join(self.__prepare_args(args))
        self.__dprint("Command: %s" % tosend)
        self.sock.send("%s%s" % (tosend, CRLF))
        for l in extralines:
            self.sock.send("%s%s" % (l, CRLF))
        code, data, content = self.__read_response(nblines)

        if withcontent:
            return (code, data, content)
        return (code, data)
  
    def __get_capabilities(self):
        code, data, capabilities = self.__read_response()
        if code == "NO":
            return False

        for l in capabilities.splitlines()[0:-2]:
            parts = l.split(None, 1)
            cname = parts[0].strip('"')
            if not cname in KNOWN_CAPABILITIES:
                continue
            self.__capabilities[cname] = \
                parts[1].strip('"') if len(parts) > 1 else None
        return True

    def __parse_error(self, text):
        """Parse an error received from the server.

        if text corresponds to a size indication, we grab the
        remaining content from the server.

        Otherwise, we try to match an error of the form \(\w+\)?\s*".+"

        On succes, the two public members errcode and errmsg are
        filled with the parsing results.

        :param text: the response to parse
        """
        m = self.__size_expr.match(text)
        if m is not None:
            self.errcode = ""
            self.errmsg = self.__read_block(int(m.group(1)) + 2)
            return

        m = self.__error_expr.match(text)
        if m is None:
            raise Error("Bad error message")
        if m.group(1) is not None:
            self.errcode = m.group(1).strip("()")
        else:
            self.errcode = ""
        self.errmsg = m.group(2).strip('"')

    def _plain_authentication(self, login, password):
        """SASL PLAIN authentication
        
        :param login: username
        :param password: clear password
        :return: True on success, False otherwise.
        """
        params = base64.b64encode('\0' + '\0'.join([login, password]))
        code, data = self.__send_command("AUTHENTICATE", ["PLAIN", params])
        if code == "OK":
            return True
        return False

    def _login_authentication(self, login, password):
        """SASL LOGIN authentication

        :param login: username
        :param password: clear password
        :return: True on success, False otherwise.
        """
        extralines = ['"%s"' % base64.b64encode(login), 
                      '"%s"' % base64.b64encode(password)]
        code, data = self.__send_command("AUTHENTICATE", ["LOGIN"], 
                                         extralines=extralines)
        if code == "OK":
            return True
        return False

    def _digest_md5_authentication(self, login, password):
        """SASL DIGEST-MD5 authentication

        :param login: username
        :param password: clear password
        :return: True on success, False otherwise.
        """
        code, data, challenge = \
            self.__send_command("AUTHENTICATE", ["DIGEST-MD5"], 
                                withcontent=True, nblines=1)
        dmd5 = DigestMD5(challenge, "sieve/%s" % self.srvaddr)
        
        code, data, challenge = \
            self.__send_command('"%s"' % dmd5.response(login, password),
                                withcontent=True, nblines=1)
        if not len(challenge):
            return False
        if not dmd5.check_last_challenge(login, password, challenge):
            self.errmsg = "Bad challenge received from server"
            return False
        code, data = self.__send_command('""')
        if code == "OK":
            return True
        return False
        
    def __authenticate(self, login, password, authmech=None):
        """AUTHENTICATE command

        Actually, it is just a wrapper to the real commands (one by
        mechanism). We try all supported mechanisms (from the
        strongest to the weakest) until we find one supported by the
        server.

        Then we try to authenticate (only once).

        :param login: username
        :param password: clear password
        :param authmech: prefered authentication mechanism
        :return: True on success, False otherwise
        """
        if not self.__capabilities.has_key("SASL"):
            raise Error("SASL not supported by the server")
        srv_mechanisms = self.get_sasl_mechanisms()

        if authmech is None or authmech not in SUPPORTED_AUTH_MECHS:
            mech_list = SUPPORTED_AUTH_MECHS
        else:
            mech_list = [authmech]

        for mech in mech_list:
            if not mech in srv_mechanisms:
                continue
            mech = mech.lower()
            mech = re.sub("-", "_", mech)
            if getattr(self, "_%s_authentication" % mech.lower())(login, password):
                self.authenticated = True
                return True
            return False
        
        self.errmsg = "No suitable mechanism found"
        return False

    def __starttls(self, keyfile=None, certfile=None):
        """STARTTLS command

        See MANAGESIEVE specifications, section 2.2.
        
        :param keyfile: an eventual private key to use
        :param certfile: an eventual certificate to use
        :rtype: boolean
        """
        if not self.has_tls_support():
            raise Error("STARTTLS not supported by the server")
        code, data = self.__send_command("STARTTLS")
        if code != "OK":
            return False
        try:
            nsock = ssl.wrap_socket(self.sock, keyfile, certfile)
        except ssl.SSLError, e:
            raise Error("SSL error: %s" % str(e))
        self.sock = nsock
        self.__capabilities = {}
        self.__get_capabilities()
        return True

    def get_implementation(self):
        """Returns the IMPLEMENTATION value.

        It is read from server capabilities. (see the CAPABILITY
        command)

        :rtype: string
        """
        return self.__capabilities["IMPLEMENTATION"]

    def get_sasl_mechanisms(self):
        """Returns the supported authentication mechanisms.

        They're read from server capabilities. (see the CAPABILITY
        command)

        :rtype: list of string
        """
        return self.__capabilities["SASL"].split()

    def has_tls_support(self):
        """Tells if the server has STARTTLS support or not.

        It is read from server capabilities. (see the CAPABILITY
        command)

        :rtype: boolean
        """
        return self.__capabilities.has_key("STARTTLS")

    def get_sieve_capabilities(self):
        """Returns the SIEVE extensions supported by the server.

        They're read from server capabilities. (see the CAPABILITY
        command)
        
        :rtype: string
        """
        if type(self.__capabilities["SIEVE"]) == str:
            self.__capabilities["SIEVE"] = self.__capabilities["SIEVE"].split()
        return self.__capabilities["SIEVE"]

    def connect(self, login, password, starttls=False, authmech=None):
        """Establish a connection with the server.

        This function must be used. It read the server capabilities
        and wraps calls to STARTTLS and AUTHENTICATE commands.

        :param login: username
        :param password: clear password
        :param starttls: use a TLS connection or not
        :param authmech: prefered authenticate mechanism
        :rtype: boolean
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.srvaddr, self.srvport))
            self.sock.settimeout(ManageSieveClient.read_timeout)
        except socket.error, msg:
            raise Error("Connection to server failed: %s" % str(msg))
        
        if not self.__get_capabilities():
            raise Error("Failed to read capabilities from server")
        if starttls and not self.__starttls():
            return False
        if self.__authenticate(login, password, authmech):
            return True
        return False

    def logout(self):
        """Disconnect from the server

        See MANAGESIEVE specifications, section 2.3
        """
        self.__send_command("LOGOUT")

    def capability(self):
        """Ask server capabilities.

        See MANAGESIEVE specifications, section 2.4 This command does
        not affect capabilities recorded by this client.

        :rtype: string
        """
        code, data, capabilities = \
            self.__send_command("CAPABILITY", withcontent=True)
        if code == "OK":
            return capabilities
        return None

    @authentication_required
    def havespace(self, scriptname, scriptsize):
        """Ask for available space.
        
        See MANAGESIEVE specifications, section 2.5

        :param scriptname: script's name
        :param scriptsize: script's size
        :rtype: boolean
        """
        code, data = self.__send_command("HAVESPACE", [scriptname, scriptsize])
        if code == "OK":
            return True
        return False

    @authentication_required
    def listscripts(self):
        """List available scripts.

        See MANAGESIEVE specifications, section 2.7

        :returns: a 2-uple (active script, [script1, ...])
        """
        code, data, listing = self.__send_command("LISTSCRIPTS", withcontent=True)
        if code == "NO":
            return None
        ret = []
        active_script = None
        for l in listing.splitlines():
            if self.__size_expr.match(l):
                continue
            m = re.match('"([^"]+)"\s*(.+)', l)
            if m is None:
                ret += [l.strip('"')]
            else:
                if self.__active_expr.match(m.group(2)):
                    active_script = m.group(1)
                else:
                    ret += [m.group(1)]
        self.__dprint(ret)
        return (active_script, ret)

    @authentication_required
    def getscript(self, name):
        """Download a script from the server

        See MANAGESIEVE specifications, section 2.9

        :param name: script's name
        :rtype: string
        :returns: the script's content on succes, None otherwise
        """
        code, data, content = self.__send_command("GETSCRIPT", [name], withcontent=True)
        if code == "OK":
            lines = content.splitlines()
            if self.__size_expr.match(lines[0]) is not None:
                lines = lines[1:]
            return "\n".join(lines)
        return None

    @authentication_required
    def putscript(self, name, content):
        """Upload a script to the server

        See MANAGESIEVE specifications, section 2.6

        :param name: script's name
        :param content: script's content
        :rtype: boolean
        """
        content = "{%d+}%s%s" % (len(content), CRLF, content)
        code, data = \
            self.__send_command("PUTSCRIPT", [name, content])
        if code == "OK":
            return True
        return False

    @authentication_required
    def deletescript(self, name):
        """Delete a script from the server

        See MANAGESIEVE specifications, section 2.10

        :param name: script's name
        :rtype: boolean
        """
        code, data = self.__send_command("DELETESCRIPT", [name])
        if code == "OK":
            return True
        return False

    @authentication_required
    def renamescript(self, oldname, newname):
        """Rename a script on the server

        See MANAGESIEVE specifications, section 2.11.1

        As this command is optional, we emulate it if the server does
        not support it.

        :param oldname: current script's name
        :param newname: new script's name
        :rtype: boolean
        """
        if self.__capabilities.has_key("RENAMESCRIPT"):
            code, data = self.__send_command("RENAMESCRIPT", [oldname, newname])
            if code == "OK":
                return True
            return False

        (active_script, scripts) = self.listscripts()
        if scripts == None or not oldname in scripts:
            self.errmsg = "Old script does not exist"
            return False
        if newname in scripts:
            self.errmsg = "New script already exists"
            return False
        oldscript = self.getscript(oldname)
        if oldscript is None:
            return False
        if not self.putscript(newname, oldscript):
            return False
        if active_script == oldname:
            if not self.setactive(newname):
                return False
        if not self.deletescript(oldname):
            return False
        return True

    @authentication_required
    def setactive(self, scriptname):
        """Define the active script

        See MANAGESIEVE specifications, section 2.8

        If scriptname is empty, the current active script is disabled,
        ie. there will be no active script anymore.

        :param scriptname: script's name
        :rtype: boolean
        """
        code, data = self.__send_command("SETACTIVE", [scriptname])
        if code == "OK":
            return True        
        return False

