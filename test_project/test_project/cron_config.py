import random

from rq.cron import register

from django.conf import settings

from modoboa.amavis import jobs as amavis_jobs
from modoboa.calendars import jobs as calendars_jobs
from modoboa.core import jobs as core_jobs
from modoboa.admin import jobs as admin_jobs
from modoboa.maillog import jobs as maillog_jobs


register(core_jobs.clean_logs, queue_name="modoboa", cron="0 0 * * *")

# Random start for this one to avoid a DDoS on the API...
minute = random.randint(1, 59)
hour = random.randint(0, 6)
register(
    core_jobs.communicate_with_public_api,
    queue_name="modoboa",
    cron=f"{minute} {hour},{hour + 12} * * *",
)

register(admin_jobs.handle_mailbox_operations, queue_name="dovecot", cron="* * * * *")

register(maillog_jobs.logparser, queue_name="modoboa", cron="*/5 * * * *")
register(maillog_jobs.update_statistics, queue_name="modoboa", cron="0 * * * *")

register(calendars_jobs.generate_rights, queue_name="modoboa", cron="*/2 * * * *")

if "modoboa.amavis" in settings.MODOBOA_APPS:
    register(amavis_jobs.qcleanup, queue="modoboa", cron="0 0 * * *")
    register(amavis_jobs.amnotify, queue="modoboa", cron="0 12 * * *")
