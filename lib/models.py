from django.db import models

class Parameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
