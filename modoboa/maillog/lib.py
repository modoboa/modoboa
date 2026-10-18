import os
import sys
import time
from pathlib import Path

from django.core.management.base import CommandError


def ensure_rrd_rootdir(path):
    """Reject an RRD directory the current process cannot write into.

    rrdtool creates a temporary file next to the destination archive, so a
    missing or unwritable parent fails with ``Cannot create temporary file``.
    The directory is not created here: the default lives under ``/tmp``, and
    creating it would keep durable statistics on a volatile path.
    """
    if not path or not Path(path).is_dir() or not os.access(path, os.W_OK):
        raise CommandError(
            f"Directory to store RRD files ({path}) is missing, is not a "
            "directory, or is not writable by the current process. Create "
            "the directory or change the rrd_rootdir setting."
        )


def date_to_timestamp(timetuple):
    """Date conversion.

    Returns a date and a time in seconds from the epoch.

    :param list timetuple: list containing date
    :return: an integer
    """
    date = " ".join(
        [str(elem) if isinstance(elem, int) else elem for elem in timetuple]
    )
    fmt = "%Y %m %d %H %M %S" if timetuple[1].isdigit() else "%Y %b %d %H %M %S"
    try:
        local = time.strptime(date, fmt)
    except ValueError:
        print("Error: failed to convert date and time", file=sys.stderr)
        return 0
    return int(time.mktime(local))
