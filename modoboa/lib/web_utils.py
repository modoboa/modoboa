"""Extra functions/shortcuts used to render HTML."""

import re


def size2integer(value: str, output_unit: str = "B") -> int:
    """
    Try to convert a string representing a size to an integer value in bytes or megabytes.

    Supported formats:
    * K|k for KB
    * M|m for MB
    * G|g for GB

    :param value: the string to convert
    :param output_unit: result's unit (defaults to Bytes)
    :return: the corresponding integer value
    """
    m = re.match(r"(\d+)\s*([a-zA-Z]+)", value)
    if m is None:
        if re.match(r"\d+", value):
            return int(value)
        return 0
    if output_unit == "B":
        if m.group(2)[0] in ["K", "k"]:
            return int(m.group(1)) * 2**10
        if m.group(2)[0] in ["M", "m"]:
            return int(m.group(1)) * 2**20
        if m.group(2)[0] in ["G", "g"]:
            return int(m.group(1)) * 2**30
    elif output_unit == "MB":
        if m.group(2)[0] in ["K", "k"]:
            return int(int(m.group(1)) / 2**10)
        if m.group(2)[0] in ["M", "m"]:
            return int(m.group(1))
        if m.group(2)[0] in ["G", "g"]:
            return int(m.group(1)) * 2**10
    else:
        raise ValueError(f"Unsupported output unit {output_unit}")
    return 0
