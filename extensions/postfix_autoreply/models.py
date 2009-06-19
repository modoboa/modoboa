from django.db import models
from mailng.admin.models import Domain, Mailbox

class Transport(models.Model):
    domain = models.CharField(max_length=300)
    method = models.CharField(max_length=255)

class Alias(models.Model):
    full_address = models.CharField(max_length=255)
    autoreply_address = models.CharField(max_length=255)
