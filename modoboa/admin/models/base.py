from django.db import models

from modoboa.lib import events
from modoboa.lib.permissions import (
    grant_access_to_object, ungrant_access_to_object
)


class ObjectDates(models.Model):

    """Dates recording for admin objects

    This table keeps creation and last modification dates for Domains,
    domain aliases, mailboxes and aliases objects.
    """
    creation = models.DateTimeField(auto_now_add=True)
    last_modification = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin"

    @staticmethod
    def set_for_object(obj):
        """Initialize or update dates for a given object.

        :param obj: an admin object (Domain, Mailbox, etc)
        """
        try:
            dates = getattr(obj, "dates")
        except ObjectDates.DoesNotExist:
            dates = ObjectDates()
        dates.save()
        obj.dates = dates


class AdminObject(models.Model):

    """Abstract model to support dates

    Inherit from this model to automatically add the "dates" feature
    to another model. It defines the appropriate field and handles
    saves.
    """
    dates = models.ForeignKey(ObjectDates)
    _objectname = None

    class Meta:
        abstract = True

    @property
    def creation(self):
        return self.dates.creation

    @property
    def last_modification(self):
        return self.dates.last_modification

    @property
    def objectname(self):
        if self._objectname is None:
            return self.__class__.__name__
        return self._objectname

    def post_create(self, creator):
        grant_access_to_object(creator, self, is_owner=True)
        events.raiseEvent("%sCreated" % self.objectname, creator, self)

    def save(self, *args, **kwargs):
        ObjectDates.set_for_object(self)
        if "creator" in kwargs:
            creator = kwargs["creator"]
            del kwargs["creator"]
        else:
            creator = None
        super(AdminObject, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def delete(self):
        events.raiseEvent("%sDeleted" % self.objectname, self)
        ungrant_access_to_object(self)
        super(AdminObject, self).delete()
