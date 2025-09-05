#!/usr/bin/env python


import time

from django.core.management.base import BaseCommand
from django.db.models import Count

from modoboa.parameters import tools as param_tools
from ...models import Maddr, Msgrcpt, Msgs


class Command(BaseCommand):
    args = ""
    help = "Amavis quarantine cleanup"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--debug", action="store_true", default=False, help="Activate debug output"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Display informational messages",
        )

    def __vprint(self, msg):
        if not self.verbose:
            return
        print(msg)

    def handle(self, *args, **options):
        if options["debug"]:
            import logging

            log = logging.getLogger("django.db.backends")
            log.setLevel(logging.DEBUG)
            log.addHandler(logging.StreamHandler())
        self.verbose = options["verbose"]

        conf = dict(param_tools.get_global_parameters("amavis"))

        flags = ["D"]
        if conf["released_msgs_cleanup"]:
            flags += ["R"]

        self.__vprint("Deleting marked messages...")
        ids = Msgrcpt.objects.filter(rs__in=flags).values("mail_id").distinct()
        for msg in Msgs.objects.filter(mail_id__in=ids):
            if not msg.msgrcpt_set.exclude(rs__in=flags).count():
                msg.delete()

        self.__vprint(
            "Deleting messages older than {} days...".format(conf["max_messages_age"])
        )
        limit = int(time.time()) - (conf["max_messages_age"] * 24 * 3600)
        while True:
            qset = Msgs.objects.filter(
                pk__in=list(
                    Msgs.objects.filter(time_num__lt=limit).values_list(
                        "pk", flat=True
                    )[:5000]
                )
            )
            if not qset.exists():
                break
            qset.delete()

        self.__vprint("Deleting unreferenced e-mail addresses...")
        while True:
            res = (
                Maddr.objects.annotate(
                    msgs_count=Count("msgs"), msgrcpt_count=Count("msgrcpt")
                )
                .filter(msgs_count=0, msgrcpt_count=0)
                .values_list("id", flat=True)[:100000]
            )
            if not res.exists():
                break
            Maddr.objects.filter(id__in=list(res)).delete()

        self.__vprint("Done.")
