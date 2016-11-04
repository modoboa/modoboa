"""Base admin models."""

from django.db import models
from django.utils import timezone

from modoboa.lib import events
from modoboa.lib.permissions import (
    grant_access_to_object, ungrant_access_to_object
)


class AdminObject(models.Model):
    """Abstract model to support dates.

    Inherit from this model to automatically add the "dates" feature
    to another model. It defines the appropriate field and handles
    saves.
    """

    creation = models.DateTimeField(default=timezone.now)
    last_modification = models.DateTimeField(auto_now=True)
    _objectname = None

    class Meta:
        abstract = True

    @property
    def objectname(self):
        if self._objectname is None:
            return self.__class__.__name__
        return self._objectname

    def post_create(self, creator):
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("%sCreated" % self.objectname, creator, self)

    def save(self, *args, **kwargs):
        creator = kwargs.pop("creator", None)
        super(AdminObject, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def delete(self):
        events.raiseEvent("%sDeleted" % self.objectname, self)
        ungrant_access_to_object(self)
        super(AdminObject, self).delete()
