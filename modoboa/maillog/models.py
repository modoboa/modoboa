"""App. related models."""

from django.db import models


class Maillog(models.Model):
    """A model to store message logs."""

    queue_id = models.CharField(max_length=50)
    date = models.DateTimeField()
    sender = models.EmailField()
    rcpt = models.EmailField()
    original_rcpt = models.EmailField(null=True)
    size = models.PositiveIntegerField()
    status = models.CharField(max_length=15)

    from_domain = models.ForeignKey(
        "admin.Domain", on_delete=models.SET_NULL, null=True,
        related_name="sent_messages_log"
    )
    to_domain = models.ForeignKey(
        "admin.Domain", on_delete=models.SET_NULL, null=True,
        related_name="recv_messages_log"
    )

    class Meta:
        ordering = ['date']
