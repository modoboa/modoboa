"""Plain text messages in format=flowed (RFC 3676).

Long lines are cut so that the message stays readable everywhere, while
clients supporting the format join them back. A line ending with a space
continues on the next one (soft break); others end a paragraph.
"""

# Lines are cut beyond this length, quote marks included
WIDTH = 72
# A line made of it is a hard break, despite its trailing space
SIGNATURE_SEPARATOR = "-- "


def _split_quote(line: str) -> tuple[int, str]:
    """Return the quote depth of a line and its content."""
    content = line.lstrip(">")
    return len(line) - len(content), content


def _wrap(content: str, width: int) -> list[str]:
    """Cut a line at spaces: each piece but the last ends with a space."""
    pieces = []
    while len(content) > width:
        pos = content.rfind(" ", 0, width)
        if pos <= 0:
            # A word longer than the line: cut after it
            pos = content.find(" ", width)
            if pos == -1:
                break
        pieces.append(content[: pos + 1])
        content = content[pos + 1 :]
    pieces.append(content)
    return pieces


def encode(text: str, width: int = WIDTH) -> str:
    """Turn a text into format=flowed lines."""
    result = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line == SIGNATURE_SEPARATOR:
            result.append(line)
            continue
        depth, content = _split_quote(line)
        if depth and content.startswith(" "):
            # The space after the quote marks is space-stuffing
            content = content[1:]
        # A trailing space would make it a soft break
        content = content.rstrip(" ")
        prefix = ">" * depth
        for piece in _wrap(content, width - depth - 1):
            # Space-stuffing: the first space of a line is removed by
            # clients, and lines starting with ">" would be quotes
            if (depth and piece) or piece.startswith((" ", ">", "From ")):
                piece = f" {piece}"
            result.append(prefix + piece)
    return "\n".join(result)


def decode(text: str, delsp: bool = False) -> str:
    """Join the lines of a format=flowed text back.

    :param delsp: the space ending soft broken lines is not part of the
        text (DelSp=Yes parameter)
    """
    paragraphs: list[list] = []
    current = None
    for line in text.replace("\r\n", "\n").split("\n"):
        depth, content = _split_quote(line)
        if content.startswith(" "):
            content = content[1:]
        flowed = content.endswith(" ") and not (
            depth == 0 and content == SIGNATURE_SEPARATOR
        )
        if flowed and delsp:
            content = content[:-1]
        if current is not None and current[0] == depth:
            current[1] += content
        else:
            if current is not None:
                # The quote depth changed after a soft break: a hard one
                paragraphs.append(current)
            current = [depth, content]
        if not flowed:
            paragraphs.append(current)
            current = None
    if current is not None:
        paragraphs.append(current)
    return "\n".join(
        ">" * depth + (" " if depth and content else "") + content
        for depth, content in paragraphs
    )
