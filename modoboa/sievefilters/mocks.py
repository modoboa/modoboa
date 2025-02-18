"""Mock objects."""

SAMPLE_SIEVE_SCRIPT = """require ["fileinto", "copy"];

# Filter: test1
if anyof (header :contains "To" "test1") {
    fileinto :copy "Test1";
}

# Filter: test2
if anyof (header :contains "To" "test2") {
    fileinto "Test2";
}

# Filter: test3
if anyof (size :over 100k) {
    fileinto "Test3";
}

# Filter: test4
if anyof (not header :contains "Sender" "toto@toto.com") {
    fileinto "Toto";
}

# Filter: test5
if true {
    fileinto "All";
}
"""

SAMPLE_SIEVE_SCRIPT2 = """require ["fileinto"];

# Filter: Tést
if anyof (header :contains "Subject" "toto", not header :contains "To" "peé") {
    fileinto "Administratif.Contrats.CIC";
    stop;
}
"""

SAMPLE_COMPLEX_SCRIPT = """require ["imap4flags"];

# Filter: Test42
if anyof (header :contains "From" "TOBESEEN") {
    setflag "\\seen";
}

"""


class ManagesieveClientMock:
    """Fake managesieve client."""

    errmsg: bytes = b""

    def __init__(self, *args, **kwargs):
        self.scripts = {
            "main_script": SAMPLE_SIEVE_SCRIPT,
            "second_script": SAMPLE_SIEVE_SCRIPT,
            "third_script": SAMPLE_SIEVE_SCRIPT2,
            "complex_script": SAMPLE_COMPLEX_SCRIPT,
        }

    def connect(self, username, password, **kwargs):
        return username == "user@test.com"

    def logout(self):
        return True

    def capability(self):
        return """
"IMPLEMENTATION" "Example1 ManageSieved v001"
"VERSION" "1.0"
"SASL" "PLAIN SCRAM-SHA-1 GSSAPI OAUTHBEARER"
"SIEVE" "fileinto vacation"
"STARTTLS"
"""

    def havespace(self, name, size):
        return True

    def listscripts(self):
        return ("main_script", ["second_script"])

    def getscript(self, name):
        return self.scripts.get(name)

    def putscript(self, name, content):
        self.scripts[name] = content
        return True

    def setactive(self, name):
        return True

    def deletescript(self, name):
        return True

    def checkscript(self, content):
        return True


class IMAP4Mock:
    """Fake IMAP4 client."""

    def __init__(self, *args, **kwargs):
        self.untagged_responses = {}

    def _quote(self, data):
        return data

    def _simple_command(self, name, *args, **kwargs):
        if name == "CAPABILITY":
            self.untagged_responses["CAPABILITY"] = [b""]
        elif name == "LIST":
            self.untagged_responses["LIST"] = [b'() "." "INBOX"']
        return "OK", None

    def list(self):
        return "OK", [b'() "." "INBOX"']
