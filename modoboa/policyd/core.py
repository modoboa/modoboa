"""Core components of the policy daemon."""

from asgiref.sync import sync_to_async
import asyncio
import concurrent.futures
from contextlib import suppress
from email.message import EmailMessage
import logging

import aiosmtplib
from dateutil.relativedelta import relativedelta
from redis import asyncio as aioredis

from django.conf import settings
from django.db import connections
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.admin import constants as admin_constants
from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.email_utils import split_mailbox

from . import constants

logger = logging.getLogger("modoboa.policyd")


SUCCESS_ACTION = b"dunno"
FAILURE_ACTION = b"defer_if_permit Daily limit reached, retry later"


def get_redis_client():
    if not getattr(settings, "REDIS_SENTINEL", False):
        return aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    sentinel = aioredis.sentinel.Sentinel(
        settings.REDIS_SENTINELS, socket_timeout=0.1, db=settings.REDIS_QUOTA_DB
    )
    return sentinel.master_for(settings.REDIS_MASTER, socket_timeout=0.1)


async def close_redis_client(rclient):
    """Close client and its connection pool (not closed by default with sentinel)."""
    await rclient.aclose(close_connection_pool=True)


def close_db_connections(func, *args, **kwargs):
    """
    Make sure to close all connections to DB.

    To use in threads.
    """

    def _close_db_connections(*args, **kwargs):
        ret = None
        try:
            ret = func(*args, **kwargs)
        finally:
            for conn in connections.all():
                conn.close()
        return ret

    return _close_db_connections


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


async def run_at(dt, coro, *args):
    """Run coroutine at given datetime."""
    await wait_for(dt)
    return await coro(*args)


@close_db_connections
def get_local_config():
    """Return local configuration."""
    return core_models.LocalConfig.objects.first()


@close_db_connections
def get_notification_recipients():
    """Return superadmins with a mailbox."""
    return core_models.User.objects.filter(is_superuser=True, mailbox__isnull=False)


@close_db_connections
def create_alarm(ltype, name):
    """Create a new alarm."""
    title = _("Daily sending limit reached")
    internal_name = constants.SENDING_LIMIT_ALARM
    if ltype == "domain":
        domain = admin_models.Domain.objects.get(name=name)
        domain.alarms.create(title=title, internal_name=internal_name)
    else:
        localpart, domain = split_mailbox(name)
        mailbox = admin_models.Mailbox.objects.get(
            address=localpart, domain__name=domain
        )
        mailbox.alarms.create(
            domain=mailbox.domain, title=title, internal_name=internal_name
        )


async def notify_limit_reached(ltype, name):
    """Send a notification to super admins about item."""
    ltype_translations = {
        "account": gettext_lazy("account"),
        "domain": gettext_lazy("domain"),
    }
    # We're going to execute sync code so we need an executor
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(executor, get_local_config),
        loop.run_in_executor(executor, get_notification_recipients),
        loop.run_in_executor(executor, create_alarm, ltype, name),
    ]
    lc, recipients, junk = await asyncio.gather(*futures)
    sender = lc.parameters.get_value("sender_address", app="core")
    for recipient in recipients:
        with translation.override(recipient.language):
            content = render_to_string(
                "policyd/notifications/limit_reached.html",
                {"ltype": ltype_translations[ltype], "name": name},
            )
            subject = _("[modoboa] Sending limit reached")
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient.email
        msg["Subject"] = subject
        msg.set_content(content)
        await aiosmtplib.send(msg)


# Atomically check that every counter can afford the message
# recipients, then decrement them. Return {1, reached_counters} on
# success, {0, {}} if a counter is too low.
DECREMENT_COUNTERS_SCRIPT = """
local count = tonumber(ARGV[1])
for i = 2, #ARGV do
  local value = redis.call('HGET', KEYS[1], ARGV[i])
  if value and tonumber(value) < count then
    return {0, {}}
  end
end
local reached = {}
for i = 2, #ARGV do
  if redis.call('HEXISTS', KEYS[1], ARGV[i]) == 1 then
    if redis.call('HINCRBY', KEYS[1], ARGV[i], -count) <= 0 then
      table.insert(reached, ARGV[i])
    end
  end
end
return {1, reached}
"""


def get_counter_keys(sasl_username):
    """Return the counter keys (domain and account) to check."""
    localpart, domain = split_mailbox(sasl_username)
    return [key for key in (domain, sasl_username) if key]


def get_recipient_count(attributes):
    """Return the number of recipients of the message."""
    try:
        return max(int(attributes.get("recipient_count", 1)), 1)
    except ValueError:
        return 1


async def check_limits(rclient, keys):
    """Refuse early if a counter is already exhausted (RCPT stage)."""
    for key in keys:
        counter = await rclient.hget(constants.REDIS_HASHNAME, key)
        if counter is None:
            continue
        logger.info(f"{key} current counter: {counter}")
        if int(counter) <= 0:
            return FAILURE_ACTION
    return SUCCESS_ACTION


async def decrement_limits(rclient, keys, count):
    """Decrement counters once the message is accepted (END-OF-MESSAGE stage)."""
    success, reached = await rclient.eval(
        DECREMENT_COUNTERS_SCRIPT, 1, constants.REDIS_HASHNAME, count, *keys
    )
    if not success:
        return FAILURE_ACTION
    for name in reached:
        if isinstance(name, bytes):
            name = name.decode()
        ltype = "account" if "@" in name else "domain"
        logger.info(f"Limit reached for {ltype} {name}")
        asyncio.ensure_future(notify_limit_reached(ltype, name))
    return SUCCESS_ACTION


async def apply_policies(attributes):
    """Apply defined policies to received request.

    Limits are checked at the RCPT stage to refuse early, but counters
    are only decremented at the END-OF-MESSAGE stage so messages
    rejected during the SMTP transaction are not counted.
    """
    sasl_username = attributes.get("sasl_username")
    if not sasl_username:
        return SUCCESS_ACTION
    keys = get_counter_keys(sasl_username)
    rclient = get_redis_client()
    try:
        if attributes.get("protocol_state") == "END-OF-MESSAGE":
            action = await decrement_limits(
                rclient, keys, get_recipient_count(attributes)
            )
        else:
            action = await check_limits(rclient, keys)
    finally:
        await close_redis_client(rclient)
    logger.debug("Action: %s", action)
    return action


async def handle_connection(reader, writer):
    """Coroutine to handle a new connection to the server."""
    action = SUCCESS_ACTION
    try:
        logger.debug("Reading data")
        data = await reader.readuntil(b"\n\n")
    except asyncio.IncompleteReadError:
        pass
    else:
        attributes = {}
        for line in data.decode().split("\n"):
            if not line:
                continue
            try:
                name, value = line.split("=")
            except ValueError:
                continue
            attributes[name] = value
        state = attributes.get("protocol_state")
        if state in ("RCPT", "END-OF-MESSAGE"):
            logger.debug("Applying policies")
            action = await apply_policies(attributes)
            logger.debug("Done")
    logger.debug("Sending action %s", action)
    writer.write(b"action=" + action + b"\n\n")
    await writer.drain()


async def new_connection(reader, writer):
    """Handle a new connection and make sure it is closed afterwards."""
    try:
        await asyncio.wait_for(handle_connection(reader, writer), timeout=5)
    except asyncio.TimeoutError:
        logger.warning("Timeout received while handling connection")
    except Exception:
        logger.exception("Error while handling connection")
    finally:
        writer.close()
        with suppress(ConnectionError):
            await writer.wait_closed()


def get_next_execution_dt():
    """Return next execution date and time."""
    return (timezone.now() + relativedelta(days=1)).replace(hour=0, minute=0, second=0)


@sync_to_async
@close_db_connections
def close_sending_limit_alarms():
    """Close all opened sending limit alarms."""
    admin_models.Alarm.objects.filter(
        internal_name=constants.SENDING_LIMIT_ALARM,
        status=admin_constants.ALARM_OPENED,
    ).update(status=admin_constants.ALARM_CLOSED, closed=timezone.now())


@sync_to_async
@close_db_connections
def get_domains_to_reset():
    """Return a list of domain to reset."""
    return list(admin_models.Domain.objects.filter(message_limit__isnull=False))


@sync_to_async
@close_db_connections
def get_mailboxes_to_reset():
    """Return a list of mailboxes to reset."""
    return list(
        admin_models.Mailbox.objects.filter(message_limit__isnull=False).select_related(
            "domain"
        )
    )


async def reset_counters():
    """Reset all counters."""
    rclient = get_redis_client()
    logger.info("Resetting all counters")
    try:
        for domain in await get_domains_to_reset():
            await rclient.hset(
                constants.REDIS_HASHNAME, domain.name, domain.message_limit
            )
        for mb in await get_mailboxes_to_reset():
            await rclient.hset(
                constants.REDIS_HASHNAME, mb.full_address, mb.message_limit
            )
        await close_sending_limit_alarms()
    except Exception:
        logger.exception("Failed to reset counters")
    finally:
        await close_redis_client(rclient)
        # reschedule
        asyncio.ensure_future(run_at(get_next_execution_dt(), reset_counters))


def start_reset_counters_coro():
    """Start coroutine."""
    first_time = (timezone.now() + relativedelta(days=1)).replace(
        hour=0, minute=0, second=0
    )
    asyncio.ensure_future(run_at(first_time, reset_counters))
