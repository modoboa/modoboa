"""Policy daemon management command."""

import asyncio
from contextlib import suppress
import functools
import logging
import signal

from django.core.management.base import BaseCommand

from ... import core

logger = logging.getLogger("modoboa.policyd")


def ask_exit(signame, loop):
    """Stop event loop."""
    loop.stop()


class Command(BaseCommand):
    """Management command for policy daemon."""

    help = "Launch Modoboa policy daemon"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument("--host", type=str, default="localhost")
        parser.add_argument("--port", type=int, default=9999)
        parser.add_argument("--socket", type=str, default=None)
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    def handle(self, *args, **options):
        """Entry point."""
        loop = asyncio.get_event_loop()
        if options["socket"] is None:
            coro = asyncio.start_server(
                core.new_connection, options["host"], options["port"]
            )
        else:
            coro = asyncio.start_unix_server(
                core.new_connection, options["socket"]
            )
        server = loop.run_until_complete(coro)

        # Schedule reset task
        core.start_reset_counters_coro()

        for signame in {"SIGINT", "SIGTERM"}:
            loop.add_signal_handler(
                getattr(signal, signame), functools.partial(ask_exit, signame, loop)
            )

        logger.info(f"Serving on {server.sockets[0].getsockname()}")

        if options["debug"]:
            loop.set_debug(True)
            logging.getLogger("asyncio").setLevel(logging.DEBUG)

        loop.run_forever()

        logger.info("Stopping policy daemon...")
        # Close the server
        server.close()
        loop.run_until_complete(server.wait_closed())
        # Cancel pending tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()
            # Await task to execute it's cancellation. Cancelled task
            # raises asyncio.CancelledError that we can suppress
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)
        loop.close()
