from django.db import models
from mailng.admin.models import Mailbox

class ARmessage(models.Model):
    mbox = models.ForeignKey(Mailbox)
    last_sent = models.DateField()
    subject = models.CharField(max_length=255)
    content = models.TextField()
