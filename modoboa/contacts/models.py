"""Contacts models."""

import os
import uuid

from dateutil.parser import parse
import vobject

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from modoboa.lib import exceptions as lib_exceptions
from modoboa.parameters import tools as param_tools

from . import constants
from .. import __version__


def generate_uid():
    return str(uuid.uuid4())


def _to_str(value):
    """vobject returns a list when a component holds several values."""
    return " ".join(value) if isinstance(value, list) else value


def _get_type(prop, choices):
    """Return the first TYPE parameter known by the model, "other" otherwise."""
    known = {choice for choice, _label in choices}
    for value in prop.params.get("TYPE", []) + prop.singletonparams:
        if value.lower() in known:
            return value.lower()
    return "other"


class AddressBook(models.Model):
    """An address book."""

    name = models.CharField(max_length=50)
    sync_token = models.TextField(blank=True)
    last_sync = models.DateTimeField(null=True)
    # Set while a sync is running (see tasks.sync_lock)
    sync_started = models.DateTimeField(null=True)
    user = models.ForeignKey("core.User", on_delete=models.CASCADE)
    _path = models.TextField()

    class Meta:
        db_table = "modoboa_contacts_addressbook"

    @property
    def syncing(self):
        return (
            self.sync_started is not None
            and self.sync_started > timezone.now() - constants.SYNC_LOCK_TIMEOUT
        )

    @property
    def url(self):
        server_location = param_tools.get_global_parameter(
            "server_location", app="calendars"
        )
        if not server_location:
            raise lib_exceptions.InternalError(
                _("Server location is not set, please fix it.")
            )
        return os.path.join(server_location, self.user.username, self._path)


class Category(models.Model):
    """A category for contacts."""

    user = models.ForeignKey("core.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "modoboa_contacts_category"


class Contact(models.Model):
    """A contact."""

    addressbook = models.ForeignKey(AddressBook, on_delete=models.CASCADE)
    uid = models.CharField(
        max_length=100, null=True, db_index=True, default=generate_uid
    )
    # Name of the vCard resource on the CardDAV server (last segment of its href)
    filename = models.CharField(max_length=255, blank=True)
    # Can't define an index on etag field because of MySQL...
    etag = models.TextField(blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    display_name = models.CharField(max_length=60, blank=True)
    birth_date = models.DateField(null=True)

    company = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=200, blank=True)

    address = models.TextField(blank=True)
    zipcode = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    note = models.TextField(blank=True)

    categories = models.ManyToManyField(Category, blank=True)

    class Meta:
        db_table = "modoboa_contacts_contact"
        constraints = [
            models.UniqueConstraint(
                fields=["addressbook", "uid"], name="unique_contact_uid_per_addressbook"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = f"{self.uid}.vcf"
        super().save(*args, **kwargs)

    def truncate_fields(self):
        """Cut external values longer than what the database accepts."""
        for field in self._meta.concrete_fields:
            value = getattr(self, field.attname)
            if isinstance(field, models.CharField) and isinstance(value, str):
                setattr(self, field.attname, value[: field.max_length])

    def to_vcard(self):
        """Convert this contact to a vCard."""
        card = vobject.vCard()
        card.add("prodid").value = f"-//Modoboa//Contacts plugin {__version__}//EN"
        card.add("uid").value = self.uid
        card.add("n").value = vobject.vcard.Name(
            family=self.last_name, given=self.first_name
        )
        card.add("fn").value = self.display_name
        card.add("org").value = [self.company]
        card.add("title").value = self.position
        card.add("adr").value = vobject.vcard.Address(
            street=self.address,
            city=self.city,
            code=self.zipcode,
            country=self.country,
            region=self.state,
        )
        if self.birth_date:
            card.add("bday").value = self.birth_date.isoformat()
        card.add("note").value = self.note
        categories = [category.name for category in self.categories.all()]
        if categories:
            card.add("categories").value = categories
        for email in EmailAddress.objects.filter(contact=self):
            attr = card.add("email")
            attr.value = email.address
            attr.type_param = email.type
        for phone in PhoneNumber.objects.filter(contact=self):
            attr = card.add("tel")
            attr.value = phone.number
            attr.type_param = phone.type
        return card.serialize()

    def update_from_vcard(self, vcard):
        """Update this contact according to given vcard.

        Fields missing from the vcard are emptied.
        """
        if hasattr(vcard, "uid"):
            self.uid = vcard.uid.value
        name = getattr(vcard, "n", None)
        self.first_name = _to_str(name.value.given) if name else ""
        self.last_name = _to_str(name.value.family) if name else ""
        address = getattr(vcard, "adr", None)
        for mfield, cfield in constants.CDAV_ADDRESS_TO_MODEL_FIELDS_MAP.items():
            value = getattr(address.value, cfield) if address else ""
            setattr(self, mfield, _to_str(value))
        self.birth_date = None
        birth_date = getattr(vcard, "bday", None)
        # Dates without year (--MMDD) can't be stored
        if birth_date and not birth_date.value.startswith("--"):
            try:
                self.birth_date = parse(birth_date.value).date()
            except (ValueError, OverflowError):
                pass
        for cfield, mfield in constants.CDAV_TO_MODEL_FIELDS_MAP.items():
            value = getattr(vcard, cfield, None)
            if not value:
                setattr(self, mfield, "")
            elif isinstance(value.value, list):
                setattr(self, mfield, value.value[0])
            else:
                setattr(self, mfield, value.value)
        self.truncate_fields()
        self.save()
        names = vcard.categories.value if hasattr(vcard, "categories") else []
        max_length = Category._meta.get_field("name").max_length
        user = self.addressbook.user
        categories = []
        for category_name in filter(None, names):
            category_name = category_name[:max_length]
            category = Category.objects.filter(user=user, name=category_name).first()
            if not category:
                category = Category.objects.create(user=user, name=category_name)
            categories.append(category)
        self.categories.set(categories)
        EmailAddress.objects.filter(contact=self).delete()
        EmailAddress.objects.bulk_create(
            EmailAddress(
                contact=self,
                address=email.value.lower(),
                type=_get_type(email, constants.EMAIL_TYPES),
            )
            for email in getattr(vcard, "email_list", [])
        )
        PhoneNumber.objects.filter(contact=self).delete()
        PhoneNumber.objects.bulk_create(
            PhoneNumber(
                contact=self,
                number=tel.value[: PhoneNumber._meta.get_field("number").max_length],
                type=_get_type(tel, constants.PHONE_TYPES),
            )
            for tel in getattr(vcard, "tel_list", [])
        )


class EmailAddress(models.Model):
    """An email address."""

    contact = models.ForeignKey(
        Contact, related_name="emails", on_delete=models.CASCADE
    )
    address = models.EmailField()
    type = models.CharField(max_length=20, choices=constants.EMAIL_TYPES)

    class Meta:
        db_table = "modoboa_contacts_emailaddress"


class PhoneNumber(models.Model):
    """A phone number."""

    contact = models.ForeignKey(
        Contact, related_name="phone_numbers", on_delete=models.CASCADE
    )
    number = models.CharField(max_length=40)
    type = models.CharField(max_length=20, choices=constants.PHONE_TYPES)

    class Meta:
        db_table = "modoboa_contacts_phonenumber"

    def __str__(self):
        return f"{self.type}: {self.number}"
