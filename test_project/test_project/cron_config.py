from rq.cron import register

from django.conf import settings

from modoboa.amavis import jobs as amavis_jobs
from modoboa.calendars import jobs as calendars_jobs
from modoboa.core import jobs as core_jobs
from modoboa.admin import jobs as admin_jobs
from modoboa.maillog import jobs as maillog_jobs
from modoboa.webmail import jobs as webmail_jobs


register(core_jobs.clean_logs, queue_name="modoboa", cron="0 0 * * *")

# Random start for this one to avoid a DDoS on the API...
register(
    core_jobs.communicate_with_public_api,
    queue_name="modoboa",
    cron="12 2,14 * * *",
)

register(admin_jobs.handle_mailbox_operations, queue_name="dovecot", cron="* * * * *")
register(admin_jobs.handle_dns_checks, queue_name="modoboa", cron="* * * * *")

register(maillog_jobs.logparser, queue_name="modoboa", cron="*/5 * * * *")
register(maillog_jobs.update_statistics, queue_name="modoboa", cron="0 * * * *")

register(calendars_jobs.generate_rights, queue_name="modoboa", cron="*/2 * * * *")

register(webmail_jobs.send_scheduled_messages, queue_name="modoboa", cron="* * * * *")

if "modoboa.amavis" in settings.MODOBOA_APPS:
    register(amavis_jobs.qcleanup, queue_name="modoboa", cron="0 0 * * *")
    register(amavis_jobs.amnotify, queue_name="modoboa", cron="0 12 * * *")
