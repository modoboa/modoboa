"""Relay domain related models."""

from django.db import models


class RecipientAccess(models.Model):
    """An recipient level access table."""

    pattern = models.CharField(unique=True, max_length=254)
    action = models.CharField(max_length=40)
