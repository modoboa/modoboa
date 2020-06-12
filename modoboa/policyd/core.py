"""Core components of the policy daemon."""

import asyncio
import concurrent.futures
from email.message import EmailMessage
import logging

import aiosmtplib
from dateutil.relativedelta import relativedelta
import aioredis

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.email_utils import split_mailbox

from . import constants

logger = logging.getLogger("modoboa.policyd")


SUCCESS_ACTION = b"dunno"
FAILURE_ACTION = b"defer_if_permit Daily limit reached, retry later"


async def wait_for(dt):
    """sleep until the specified datetime."""
    one_day = 86400
    while True:
        now = timezone.now()
        remaining = (dt - now).total_seconds()
        if remaining < one_day:
            break
        # asyncio.sleep doesn't like long sleeps, so don't sleep more
        # than a day at a time
        await asyncio.sleep(one_day)
    await asyncio.sleep(remaining)


async def run_at(dt, coro):
    """Run coroutine at given datetime."""
    await wait_for(dt)
    return await coro()


def get_local_config():
    """Return local configuration."""
    return core_models.LocalConfig.objects.first()


def get_notification_recipients():
    """Return superadmins with a mailbox."""
    return (
        core_models.User.objects
        .filter(is_superuser=True, mailbox__isnull=False)
    )


async def notify_limit_reached(ltype, name):
    """Send a notification to super admins about item."""
    ltype_translations = {
        "account": ugettext_lazy("account"),
        "domain": ugettext_lazy("domain")
    }
    # We're going to execute sync code so we need an executor
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_running_loop()
    futures = [
        loop.run_in_executor(executor, get_local_config),
        loop.run_in_executor(executor, get_notification_recipients)
    ]
    lc, recipients = await asyncio.gather(*futures)
    sender = lc.parameters.get_value("sender_address", app="core")
    for recipient in recipients:
        with translation.override(recipient.language):
            content = render_to_string(
                "policyd/notifications/limit_reached.html", {
                    "ltype": ltype_translations[ltype], "name": name
                })
            subject = _("[modoboa] Sending limit reached")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient.email
        msg["Subject"] = subject
        msg.set_content(content)
        await aiosmtplib.send(msg)


async def decrement_limit(rclient, ltype, name):
    """Decrement the given limit by one."""
    new_counter = await rclient.hincrby(constants.REDIS_HASHNAME, name, -1)
    if new_counter <= 0:
        logger.info("Limit reached for {} {}".format(ltype, name))
        loop = asyncio.get_running_loop()
        loop.create_task(notify_limit_reached(ltype, name))


async def apply_policies(attributes):
    """Apply defined policies to received request."""
    sasl_username = attributes.get("sasl_username")
    if not sasl_username:
        return SUCCESS_ACTION
    rclient = await aioredis.create_redis_pool(settings.REDIS_URL)
    decr_domain = False
    decr_user = False
    localpart, domain = split_mailbox(sasl_username)
    if await rclient.hexists(constants.REDIS_HASHNAME, domain):
        counter = await rclient.hget(constants.REDIS_HASHNAME, domain)
        logger.info("Domain {} current counter: {}".format(domain, counter))
        if int(counter) <= 0:
            return FAILURE_ACTION
        decr_domain = True
    if await rclient.hexists(constants.REDIS_HASHNAME, sasl_username):
        counter = await rclient.hget(constants.REDIS_HASHNAME, sasl_username)
        logger.info("Account {} current counter: {}".format(
            sasl_username, counter))
        if int(counter) <= 0:
            return FAILURE_ACTION
        decr_user = True
    if decr_domain:
        await decrement_limit(rclient, "domain", domain)
    if decr_user:
        await decrement_limit(rclient, "account", sasl_username)
    return SUCCESS_ACTION


async def process_messages(queue):
    """Pull from queue and process messages."""
    while True:
        transport, message = await queue.get()
        result = await apply_policies(message)
        transport.write(b"action=" + result + b"\n\n")
        queue.task_done()


class APDProtocol(asyncio.Protocol):
    """Access Policy Delegation protocol (postfix)."""

    def __init__(self, *args, **kwargs):
        """Store queue."""
        self.queue = kwargs.pop("queue")
        super().__init__(*args, **kwargs)

    def connection_made(self, transport):
        peername = transport.get_extra_info("peername")
        logger.info("Connection from {}".format(peername))
        self.transport = transport

    def data_received(self, data):
        attributes = {}
        for line in data.decode().split("\n"):
            if not line:
                continue
            try:
                name, value = line.split("=")
            except ValueError:
                continue
            attributes[name] = value

        # action = SUCCESS_ACTION
        state = attributes.get("protocol_state")
        if state == "RCPT":
            self.queue.put_nowait((self.transport, attributes))
        else:
            self.transport.write(b"action=" + SUCCESS_ACTION + b"\n\n")


def get_next_execution_dt():
    """Return next execution date and time."""
    return (timezone.now() + relativedelta(days=1)).replace(
        hour=0, minute=0, second=0)


def get_domains_to_reset():
    """Return a list of domain to reset."""
    return admin_models.Domain.objects.filter(message_limit__isnull=False)


def get_mailboxes_to_reset():
    """Return a list of mailboxes to reset."""
    return (
        admin_models.Mailbox.objects.filter(message_limit__isnull=False)
        .select_related("domain")
    )


async def reset_counters():
    """Reset all counters."""
    rclient = await aioredis.create_redis_pool(settings.REDIS_URL)
    logger.info("Resetting all counters")
    # We're going to execute sync code so we need an executor
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_running_loop()
    futures = [
        loop.run_in_executor(executor, get_domains_to_reset),
        loop.run_in_executor(executor, get_mailboxes_to_reset)
    ]
    domains, mboxes = await asyncio.gather(*futures)
    for domain in domains:
        rclient.hset(
            constants.REDIS_HASHNAME, domain.name, domain.message_limit)
    for mb in mboxes:
        rclient.hset(
            constants.REDIS_HASHNAME, mb.full_address, mb.message_limit)
    # reschedule
    loop = asyncio.get_running_loop()
    loop.create_task(run_at(get_next_execution_dt(), reset_counters))


def start_reset_counters_coro(loop):
    """Start coroutine."""
    first_time = (timezone.now() + relativedelta(days=1)).replace(
        hour=0, minute=0, second=0)
    loop.create_task(run_at(first_time, reset_counters))
