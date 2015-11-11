import os.path
import sys
import csv
from progressbar import ProgressBar, Percentage, Bar, ETA

from modoboa.core.models import User
from modoboa.lib import events
from modoboa.lib.exceptions import Conflict

from ... import lib


def import_csv(filename, options):
    """Import objects from a CSV file."""
    superadmin = User.objects.filter(is_superuser=True).first()
    if not os.path.exists(filename):
        print('File not found')
        sys.exit(1)

    num_lines = sum(1 for line in open(filename))
    pbar = ProgressBar(
        widgets=[Percentage(), Bar(), ETA()], maxval=num_lines
    ).start()
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        i = 0
        for row in reader:
            i += 1
            pbar.update(i)
            if not row:
                continue

            try:
                fct = getattr(lib, "import_%s" % row[0].strip())
            except AttributeError:
                fct = events.raiseQueryEvent(
                    'ImportObject', row[0].strip())
                if not fct:
                    continue
                fct = fct[0]

            try:
                fct(superadmin, row, options)
            except Conflict:
                if options['continue_if_exists']:
                    continue

                raise Conflict(
                    "Object already exists: %s"
                    % options['sepchar'].join(row[:2])
                )

    pbar.finish()
