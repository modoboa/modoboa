"""Base admin models."""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from modoboa.core import models as core_models
from modoboa.lib.permissions import (
    grant_access_to_object, ungrant_access_to_object
)


class AdminObjectManager(models.Manager):

    def get_for_admin(self, admin):
        """Return the objects belonging to this admin

        The result is a ``QuerySet`` object, so this function can be used
        to fill ``ModelChoiceField`` objects.
        """
        if admin.is_superuser:
            return self.get_queryset()
        return self.get_queryset().filter(owners__user=admin)


class AdminObject(models.Model):
    """Abstract model to support dates.

    Inherit from this model to automatically add the "dates" feature
    to another model. It defines the appropriate field and handles
    saves.
    """

    creation = models.DateTimeField(default=timezone.now)
    last_modification = models.DateTimeField(auto_now=True)
    owners = GenericRelation(core_models.ObjectAccess)
    _objectname = None

    objects = AdminObjectManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """Custom constructor."""
        super().__init__(*args, **kwargs)
        self._loaded_values = {}

    @classmethod
    def from_db(cls, db, field_names, values):
        """Store loaded values."""
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    @property
    def objectname(self):
        if self._objectname is None:
            return self.__class__.__name__
        return self._objectname

    def post_create(self, creator):
        grant_access_to_object(creator, self, is_owner=True)

    def save(self, *args, **kwargs):
        creator = kwargs.pop("creator", None)
        super(AdminObject, self).save(*args, **kwargs)
        if creator is not None:
            self.post_create(creator)

    def delete(self):
        ungrant_access_to_object(self)
        super(AdminObject, self).delete()
