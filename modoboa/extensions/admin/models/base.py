from django.db import models


class ObjectDates(models.Model):
    """Dates recording for admin objects

    This table keeps creation and last modification dates for Domains,
    domain aliases, mailboxes and aliases objects.
    """
    creation = models.DateTimeField(auto_now_add=True)
    last_modification = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'admin'

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


class DatesAware(models.Model):
    """Abstract model to support dates

    Inherit from this model to automatically add the "dates" feature
    to another model. It defines the appropriate field and handles
    saves.
    """
    dates = models.ForeignKey(ObjectDates)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        ObjectDates.set_for_object(self)
        super(DatesAware, self).save(*args, **kwargs)

    @property
    def creation(self):
        return self.dates.creation

    @property
    def last_modification(self):
        return self.dates.last_modification
