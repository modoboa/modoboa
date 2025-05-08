"""Mock objects."""

from modoboa.webmail.tests import data as tests_data


class IMAP4Mock:
    """Fake IMAP4 client."""

    def __init__(self, *args, **kwargs):
        self.untagged_responses = {}

    def _quote(self, data):
        return data

    def _simple_command(self, name, *args, **kwargs):
        if name == "CAPABILITY":
            self.untagged_responses["CAPABILITY"] = [b"QUOTA"]
        elif name == "LIST":
            self.untagged_responses["LIST"] = [b'() "." "INBOX"']
        elif name == "NAMESPACE":
            self.untagged_responses["NAMESPACE"] = [b'(("" "/")) NIL NIL']
        elif name == "STATUS":
            self.untagged_responses["STATUS"] = [b"STATUS INBOX (UNSEEN 10)"]
        return "OK", None

    def append(self, *args, **kwargs):
        pass

    def create(self, name):
        return "OK", None

    def delete(self, name):
        return "OK", None

    def list(self):
        return "OK", [b'() "." "INBOX"']

    def rename(self, oldname, newname):
        return "OK", None

    def uid(self, command, *args):
        if command in ["SEARCH", "SORT"]:
            return "OK", [b"19"]
        elif command == "FETCH":
            uid = int(args[0])
            data = tests_data.BODYSTRUCTURE_SAMPLE_WITH_FLAGS
            if uid == 46931:
                if args[1] == "(BODYSTRUCTURE)":
                    data = tests_data.BODYSTRUCTURE_ONLY_4
                elif "HEADER.FIELDS" in args[1]:
                    data = tests_data.BODYSTRUCTURE_SAMPLE_4
                else:
                    data = tests_data.BODY_PLAIN_4
            elif uid == 46932:
                if args[1] == "(BODYSTRUCTURE)":
                    data = tests_data.BODYSTRUCTURE_ONLY_5
                elif "HEADER.FIELDS" in args[1]:
                    data = tests_data.BODYSTRUCTURE_SAMPLE_9
                else:
                    data = tests_data.BODYSTRUCTURE_SAMPLE_10
            elif uid == 33:
                if args[1] == "(BODYSTRUCTURE)":
                    data = tests_data.BODYSTRUCTURE_EMPTY_MAIL
                elif "HEADER.FIELDS" in args[1]:
                    data = tests_data.BODYSTRUCTURE_EMPTY_MAIL_WITH_HEADERS
                else:
                    data = tests_data.EMPTY_BODY
            elif uid == 3444:
                data = tests_data.BODYSTRUCTURE_WITH_PDF
            elif uid == 133872:
                data = tests_data.COMPLETE_MAIL
            return "OK", data
        elif command in ["COPY", "STORE"]:
            return "OK", []
