"""Management command to update various statistics."""

import os

from dateutil.relativedelta import relativedelta
import rrdtool

from django.core.management.base import BaseCommand
from django.utils import timezone

from modoboa.core import models as core_models
from modoboa.parameters import tools as param_tools


class Command(BaseCommand):
    """Update statistics."""

    help = "Update modoboa statistics"

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--rebuild", action="store_true",
            help="Rebuild statistics from the begining")

    def _create_new_accounts_rrd_file(self, fname, start):
        """Create RRD file."""
        step = 3600
        ds_name = "new_accounts"
        params = ["DS:{}:ABSOLUTE:{}:0:U".format(ds_name, step * 2)]
        params += [
            "RRA:AVERAGE:0.5:1:48",     # 48 hours with a 1h granularity
            "RRA:AVERAGE:0.5:24:31",    # 31 days with a 1d granularity
            "RRA:AVERAGE:0.5:168:52",   # 52 weeks with a 1w granularity
            "RRA:AVERAGE:0.5:5208:24",  # 24 months with a 1m granularity
        ]
        rrdtool.create(
            str(fname), "--start", str(start), "--step", str(step),
            *params
        )

    def update_account_creation_stats(self, rebuild=False):
        """Look for newly created accounts."""
        db_path = os.path.join(self.rootdir, "new_accounts.rrd")
        data = []
        if not rebuild:
            end = timezone.now().replace(minute=0, second=0, microsecond=0)
            start = end - relativedelta(hours=1)
            new_accounts = core_models.User.objects.filter(
                date_joined__gte=start, date_joined__lt=end).count()
            data.append(
                "{}:{}".format(int(end.strftime("%s")), new_accounts * 60))
        else:
            existing_stats = {}
            start = None
            for user in core_models.User.objects.all().order_by("date_joined"):
                hour = user.date_joined.replace(
                    minute=0, second=0, microsecond=0) + relativedelta(hours=1)
                if start is None:
                    start = hour
                hour = int(hour.strftime("%s"))
                if hour not in existing_stats:
                    existing_stats[hour] = 0
                existing_stats[hour] += 1
            end = timezone.now().replace(
                minute=0, second=0, microsecond=0) + relativedelta(hours=1)
            if os.path.exists(db_path):
                os.unlink(db_path)
            hour = start
            while hour <= end:
                new_accounts = existing_stats.get(int(hour.strftime("%s")), 0)
                data.append("{}:{}".format(
                    int(hour.strftime("%s")), new_accounts * 60))
                hour += relativedelta(hours=1)
        if not os.path.exists(db_path):
            self._create_new_accounts_rrd_file(
                db_path, int((start - relativedelta(hours=1)).strftime("%s"))
            )
        rrdtool.update(str(db_path), *data)

    def handle(self, *args, **options):
        """Entry point."""
        self.rootdir = param_tools.get_global_parameter("rrd_rootdir")
        self.update_account_creation_stats(options["rebuild"])
