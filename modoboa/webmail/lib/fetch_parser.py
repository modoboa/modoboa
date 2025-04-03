"""Simple parser for FETCH responses.

The ``imaplib`` module doesn't parse IMAP responses, it returns raw
values. Since Modoboa relies on BODYSTRUCTURE attributes to display
messages (we don't want to overload the server), a parser is required.

Python 2/3 compatibility note: this parser excepts bytes objects when
run with Python3 and str (not unicode) ones with Python2.
"""

import re

import chardet
import six


class ParseError(Exception):
    """Generic parsing error."""

    pass


class Lexer:
    """The lexical analysis part.

    This class provides a simple way to define tokens (with patterns)
    to be detected. Patterns are provided using a list of 2-uple. Each
    2-uple consists of a token name and an associated pattern.

    Example: [("left_bracket", r'\['),]
    """

    def __init__(self, definitions):
        self.definitions = definitions
        parts = []
        for name, part in definitions:
            parts.append(rf"(?P<{name}>{part})")
        self.regexpString = "|".join(parts)
        self.regexp = re.compile(self.regexpString, re.MULTILINE)
        self.wsregexp = re.compile(r"\s+", re.M)

    def curlineno(self):
        """Return the current line number"""
        return self.text[: self.pos].count("\n") + 1

    def scan(self, text):
        """Analyze some data.

        Analyse the passed content. Each time a token is recognized, a
        2-uple containing its name and the parsed value is raised
        (using yield).

        :param text: a string containing the data to parse
        :raises: ParseError
        """
        self.pos = 0
        self.text = text
        while self.pos < len(text):
            m = self.wsregexp.match(text, self.pos)
            if m is not None:
                self.pos = m.end()
                continue

            m = self.regexp.match(text, self.pos)
            if m is None:
                raise ParseError(f"unknown token {text[self.pos :]}")

            self.pos = m.end()
            yield (m.lastgroup, m.group(m.lastgroup))


class FetchResponseParser:
    """A token generator.

    By *token*, I mean: *literal*, *quoted* or anything else until the
    next ' ' or ')' character (number, NIL and others should fall into
    this last category).
    """

    rules = [
        ("left_parenthesis", r"\("),
        ("right_parenthesis", r"\)"),
        ("string", r'"([^"\\]|\\.)*"'),
        ("nil", r"NIL"),
        (
            "data_item",
            r"(?P<name>[A-Z][A-Z\.0-9]+)"
            r"(?P<section>\[.*\])?(?P<origin_octet>\<\d+\>)?",
        ),
        ("number", r"[0-9]+"),
        ("literal_marker", r"{\d+}"),
        ("flag", r"(\\|\$)?[a-zA-Z0-9\-_]+"),
    ]

    def __init__(self):
        """Constructor."""
        self.lexer = Lexer(self.rules)
        self.__reset_parser()

    def __reset_parser(self):
        """Reset parser states."""
        self.result = {}
        self.__current_message = {}
        self.__next_literal_len = 0
        self.__cur_data_item = None
        self.__args_parsing_func = None
        self.__expected = None
        self.__depth = 0
        self.__bs_stack = []

    def set_expected(self, *args):
        """Indicate next expected token types."""
        self.__expected = args

    def __default_args_parser(self, ttype, tvalue):
        """Default arguments parser."""
        self.__current_message[self.__cur_data_item] = tvalue
        self.__args_parsing_func = None

    def __flags_args_parser(self, ttype, tvalue):
        """FLAGS arguments parser."""
        if ttype == "left_parenthesis":
            self.__current_message[self.__cur_data_item] = []
            self.__depth += 1
        elif ttype == "flag":
            self.__current_message[self.__cur_data_item].append(tvalue)
            self.set_expected("flag", "right_parenthesis")
        elif ttype == "right_parenthesis":
            self.__args_parsing_func = None
            self.__depth -= 1
        else:
            raise ParseError(f"Unexpected token found: {ttype}")

    def __set_part_numbers(self, bs, prefix=""):
        """Set part numbers."""
        cpt = 1
        for mp in bs:
            if isinstance(mp, list):
                self.__set_part_numbers(mp, prefix)
            elif isinstance(mp, dict):
                if isinstance(mp["struct"][0], list):
                    nprefix = f"{prefix}{cpt}."
                    self.__set_part_numbers(mp["struct"][0], nprefix)
                mp["partnum"] = f"{prefix}{cpt}"
                cpt += 1

    def __bstruct_args_parser(self, ttype, tvalue):
        """BODYSTRUCTURE arguments parser."""
        if ttype == "left_parenthesis":
            self.__bs_stack = [[]] + self.__bs_stack
            return
        if ttype == "right_parenthesis":
            if len(self.__bs_stack) > 1:
                part = self.__bs_stack.pop(0)
                # Check if we are parsing a list of mime part or a
                # list or arguments.
                condition = len(self.__bs_stack[0]) > 0 and not isinstance(
                    self.__bs_stack[0][0], dict
                )
                if condition:
                    self.__bs_stack[0].append(part)
                else:
                    self.__bs_stack[0].append({"struct": part})
            else:
                # End of BODYSTRUCTURE
                if not isinstance(self.__bs_stack[0][0], list):
                    # Special case for non multipart structures
                    self.__bs_stack[0] = {"struct": self.__bs_stack[0]}
                self.__set_part_numbers(self.__bs_stack)
                self.__current_message[self.__cur_data_item] = self.__bs_stack
                self.__bs_stack = []
                self.__args_parsing_func = None
            return
        if ttype == "string":
            tvalue = tvalue.strip('"')
            # Check if previous element was a mime part. If so, we are
            # dealing with a 'multipart' mime part...
            condition = len(self.__bs_stack[0]) and isinstance(
                self.__bs_stack[0][-1], dict
            )
            if condition:
                self.__bs_stack[0] = [self.__bs_stack[0]] + [tvalue]
                return
        elif ttype == "number":
            tvalue = int(tvalue)
        self.__bs_stack[0].append(tvalue)

    def __parse_data_item(self, ttype, tvalue):
        """Find next data item."""
        if ttype == "data_item":
            self.__cur_data_item = tvalue
            if tvalue == "BODYSTRUCTURE":
                self.set_expected("left_parenthesis")
                self.__args_parsing_func = self.__bstruct_args_parser
            elif tvalue == "FLAGS":
                self.set_expected("left_parenthesis")
                self.__args_parsing_func = self.__flags_args_parser
            else:
                self.__args_parsing_func = self.__default_args_parser
            return
        elif ttype == "right_parenthesis":
            self.__depth -= 1
            assert self.__depth == 0
            # FIXME: sometimes, FLAGS are returned outside the UID
            # scope (see sample 1 in tests). For now, we just ignore
            # them but we need a better solution!
            if "UID" in self.__current_message:
                self.result[int(self.__current_message.pop("UID"))] = (
                    self.__current_message
                )
            self.__current_message = {}
            return
        raise ParseError(
            f"unexpected {ttype} found while looking for data_item near {tvalue}"
        )

    def __convert_to_str(self, chunk):
        """Convert chunk to str and guess encoding."""
        condition = (
            six.PY2
            and isinstance(chunk, six.text_type)
            or six.PY3
            and isinstance(chunk, six.binary_type)
        )
        if not condition:
            return chunk
        try:
            chunk = chunk.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            return chunk
        try:
            result = chardet.detect(chunk)
        except UnicodeDecodeError:
            raise RuntimeError("Can't find string encoding") from None
        return chunk.decode(result["encoding"])

    def parse_chunk(self, chunk):
        """Parse chunk."""
        if not chunk:
            return
        chunk = self.__convert_to_str(chunk)
        if self.__next_literal_len:
            literal = chunk[: self.__next_literal_len]
            chunk = chunk[self.__next_literal_len :]
            self.__next_literal_len = 0
            if self.__cur_data_item != "BODYSTRUCTURE":
                self.__current_message[self.__cur_data_item] = literal
                self.__args_parsing_func = None
            else:
                self.__args_parsing_func("literal", literal)
        for ttype, tvalue in self.lexer.scan(chunk):
            if self.__expected is not None:
                if ttype not in self.__expected:
                    raise ParseError(
                        "unexpected {} found while looking for {}".format(
                            ttype, "|".join(self.__expected)
                        )
                    )
                self.__expected = None
            if ttype == "literal_marker":
                self.__next_literal_len = int(tvalue[1:-1])
                continue
            elif self.__depth == 0:
                if ttype == "number":
                    # We should start here with a message ID
                    self.set_expected("left_parenthesis")
                if ttype == "left_parenthesis":
                    self.__depth += 1
                continue
            elif self.__args_parsing_func is None:
                self.__parse_data_item(ttype, tvalue)
                continue
            self.__args_parsing_func(ttype, tvalue)

    def parse(self, data):
        """Parse received data."""
        self.__reset_parser()
        for chunk in data:
            if isinstance(chunk, tuple):
                for schunk in chunk:
                    self.parse_chunk(schunk)
            else:
                self.parse_chunk(chunk)
        return self.result
