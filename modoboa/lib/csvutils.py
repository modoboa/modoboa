"""Helpers to safely produce CSV files.

These utilities neutralize spreadsheet formula injection (CSV injection,
CWE-1236). Standard CSV quoting preserves field boundaries but does *not*
prevent a spreadsheet application from evaluating a cell whose content starts
with a formula trigger character.
"""

from django.utils.encoding import smart_str

# Characters a spreadsheet may interpret as the start of a formula. Leading
# tab / carriage return / newline are included because they can be used to
# smuggle one of the other triggers past naive checks.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def escape_csv_cell(value):
    """Neutralize formula triggers in a single CSV cell.

    Any value starting with a formula trigger character is prefixed with a
    single quote so spreadsheet applications render it as plain text.
    """
    value = smart_str(value)
    if value and value[0] in FORMULA_PREFIXES:
        return "'" + value
    return value


def escape_csv_row(row):
    """Return a copy of ``row`` with every cell escaped."""
    return [escape_csv_cell(cell) for cell in row]


class SafeCSVWriter:
    """Wrap a ``csv.writer`` to escape every cell before writing it."""

    def __init__(self, writer):
        self._writer = writer

    def writerow(self, row):
        return self._writer.writerow(escape_csv_row(row))

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
