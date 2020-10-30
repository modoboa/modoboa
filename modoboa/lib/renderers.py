"""Custom renderers for DRF."""

import csv
from io import StringIO

from rest_framework import renderers


class CSVRenderer(renderers.BaseRenderer):
    """Custom CSV renderer."""

    media_type = "text/csv"
    format = "csv"

    def render(self, data, media_type=None, renderer_context=None):
        if renderer_context is None:
            renderer_context = {}
        headers = renderer_context.get("headers")
        with StringIO() as fp:
            csvwriter = csv.writer(fp)
            for item in data:
                if headers is None:
                    headers = item.keys()
                row = ["domainalias"]
                for header in headers:
                    if "__" in header:
                        parts = header.split("__")
                        value = item
                        for part in parts:
                            value = value.get(part)
                    else:
                        value = item.get(header)
                    row.append(value)
                csvwriter.writerow(row)
            content = fp.getvalue()
        return content
