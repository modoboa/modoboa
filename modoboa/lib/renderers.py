"""Custom renderers for DRF."""

import csv
from io import StringIO

from rest_framework import renderers

from .csvutils import escape_csv_row


class CSVRenderer(renderers.BaseRenderer):
    """Custom CSV renderer."""

    media_type = "text/csv"
    format = "csv"

    def render(self, data, media_type=None, renderer_context=None):
        with StringIO() as fp:
            csvwriter = csv.writer(fp)
            for item in data:
                csvwriter.writerow(escape_csv_row(item))
            content = fp.getvalue()
        return content
