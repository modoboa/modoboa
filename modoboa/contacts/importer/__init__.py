import csv
from typing import Optional

from modoboa.contacts.importer.backends.outlook import OutlookBackend


BACKENDS = [
    OutlookBackend,
]


def get_import_backend(fp, delimiter: str = ";", name: str = "auto"):
    reader = csv.DictReader(fp, delimiter=delimiter, skipinitialspace=True)
    columns = reader.fieldnames
    rows = reader

    for backend in BACKENDS:
        if name == "auto":
            if backend.detect_from_columns(columns):
                return backend, rows
        elif name == backend.name:
            return backend, rows

    raise RuntimeError("Failed to detect backend to use")


def import_csv_file(
    addressbook,
    backend_name: str,
    csv_filename: str,
    delimiter: str,
    carddav_password: Optional[str] = None,
):
    with open(csv_filename) as fp:
        backend, rows = get_import_backend(fp, delimiter, backend_name)
        backend(addressbook).proceed(rows, carddav_password)
