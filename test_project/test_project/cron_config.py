from rq.cron import register

from modoboa.core import jobs as core_jobs
from modoboa.admin import jobs as admin_jobs
from modoboa.maillog import jobs as maillog_jobs


register(core_jobs.clean_logs, queue_name="modoboa", cron="0 0 * * *")

register(admin_jobs.handle_mailbox_operations, queue_name="dovecot", cron="* * * * *")

register(maillog_jobs.logparser, queue_name="modoboa", cron="*/5 * * * *")
register(maillog_jobs.update_statistics, queue_name="modoboa", cron="0 * * * *")
