from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from modoboa.extensions.admin.models import Mailbox


class Transport(models.Model):
    domain = models.CharField(max_length=300)
    method = models.CharField(max_length=255)


class Alias(models.Model):
    full_address = models.CharField(max_length=255)
    autoreply_address = models.CharField(max_length=255)


class ARmessage(models.Model):
    mbox = models.ForeignKey(Mailbox)
    subject = models.CharField(
        _('subject'), max_length=255,
        help_text=_("The subject that will appear in sent emails")
    )
    content = models.TextField(
        _('content'),
        help_text=_("The content that will appear in sent emails")
    )
    enabled = models.BooleanField(
        _('enabled'),
        help_text=_("Activate/Deactivate your auto reply")
    )
    fromdate = models.DateTimeField(default=timezone.now)
    untildate = models.DateTimeField(null=True, blank=True)


class ARhistoric(models.Model):
    armessage = models.ForeignKey(ARmessage)
    last_sent = models.DateTimeField(auto_now=True)
    sender = models.CharField(max_length=254)

    class Meta:
        unique_together = ("armessage", "sender")
