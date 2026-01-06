from rq.cron import register

from modoboa.core import jobs as core_jobs
from modoboa.admin import jobs as admin_jobs


register(admin_jobs.handle_mailbox_operations, queue_name="dovecot", cron="* * * * *")
register(core_jobs.clean_logs, queue_name="modoboa", cron="0 0 * * *")
