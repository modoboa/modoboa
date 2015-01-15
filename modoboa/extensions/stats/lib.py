# coding: utf-8
import sys
import time


def date_to_timestamp(timetuple):
    """Date conversion.

    Returns a date and a time in seconds from the epoch.

    :param list timetuple: list containing date
    :return: an integer
    """
    date = " ".join(
        [("%d" % elem) if isinstance(elem, int) else elem for elem in timetuple]
    )
    fmt = "%Y %m %d %H %M %S" \
          if timetuple[1].isdigit() else "%Y %b %d %H %M %S"
    try:
        local = time.strptime(date, fmt)
    except ValueError:
        print >> sys.stderr, "Error: failed to convert date and time"
        return 0
    return int(time.mktime(local))
