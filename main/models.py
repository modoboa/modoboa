from django.db import models
from mailng.admin.models import Mailbox

class ARmessage(models.Model):
    mbox = models.ForeignKey(Mailbox)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    enabled = models.BooleanField()

class ARhistoric(models.Model):
    armessage = models.ForeignKey(ARmessage)
    last_sent = models.DateTimeField(auto_now=True)
    sender = models.TextField()
