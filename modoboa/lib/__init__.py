# coding: utf-8
import hashlib

def md5crypt(password, salt, magic='$1$'):
    """Taken from:
    http://code.activestate.com/recipes/325204-passwd-file-compatible-1-md5-crypt/

    Based on FreeBSD src/lib/libcrypt/crypt.c 1.2
    http://www.freebsd.org/cgi/cvsweb.cgi/~checkout~/src/lib/libcrypt/crypt.c?rev=1.2&content-type=text/plain

    Original license:
    * "THE BEER-WARE LICENSE" (Revision 42):
    * <phk@login.dknet.dk> wrote this file.  As long as you retain this notice you
    * can do whatever you want with this stuff. If we meet some day, and you think
    * this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
    
    "A port of Poul-Henning Kamp's MD5 password hash routine, as initially
    found in FreeBSD 2. It is also used in Cisco routers, Apache htpasswd files,
    and other places that you find "$1$" at the beginning of password hashes."
    by Mark Johnston
    """
    # The password first, since that is what is most unknown
    # Then our magic string. Then the raw salt.
    m = hashlib.md5()
    m.update(password + magic + salt)

    # /* Then just as many characters of the MD5(pw,salt,pw) */
    mixin = hashlib.md5(password + salt + password).digest()
    for i in range(0, len(password)):
        m.update(mixin[i % 16])

    # Then something really weird... Also really broken, as far as I
    # can tell.  -m
    i = len(password)
    while i:
        if i & 1:
            m.update('\x00')
        else:
            m.update(password[0])
        i >>= 1

    final = m.digest()

    # And now, just to make sure things don't run too fast
    for i in range(1000):
        m2 = hashlib.md5()
        if i & 1:
            m2.update(password)
        else:
            m2.update(final)

        if i % 3:
            m2.update(salt)

        if i % 7:
            m2.update(password)

        if i & 1:
            m2.update(final)
        else:
            m2.update(password)

        final = m2.digest()

    # This is the bit that uses to64() in the original code.

    itoa64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    rearranged = ''
    for a, b, c in ((0, 6, 12), (1, 7, 13), (2, 8, 14), (3, 9, 15), (4, 10, 5)):
        v = ord(final[a]) << 16 | ord(final[b]) << 8 | ord(final[c])
        for i in range(4):
            rearranged += itoa64[v & 0x3f]; v >>= 6

    v = ord(final[11])
    for i in range(2):
        rearranged += itoa64[v & 0x3f]; v >>= 6

    return magic + salt + '$' + rearranged
