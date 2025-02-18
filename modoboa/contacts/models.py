"""Contacts models."""

import os
import uuid

from dateutil.parser import parse
import vobject

from django.db import models
from django.utils.translation import gettext as _

from modoboa.lib import exceptions as lib_exceptions
from modoboa.parameters import tools as param_tools

from . import constants
from .. import __version__


class AddressBook(models.Model):
    """An address book."""

    name = models.CharField(max_length=50)
    sync_token = models.TextField(blank=True)
    last_sync = models.DateTimeField(null=True)
    user = models.ForeignKey("core.User", on_delete=models.CASCADE)
    _path = models.TextField()

    class Meta:
        db_table = "modoboa_contacts_addressbook"

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
    uid = models.CharField(max_length=100, unique=True, null=True, db_index=True)
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

    def __init__(self, *args, **kwargs):
        """Set uid for new object."""
        super().__init__(*args, **kwargs)
        if not self.pk:
            self.uid = f"{uuid.uuid4()}.vcf"

    @property
    def url(self):
        return f"{self.addressbook.url}/{self.uid}.vcf"

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
        for email in EmailAddress.objects.filter(contact=self):
            attr = card.add("email")
            attr.value = email.address
            attr.type_param = email.type
        for phone in PhoneNumber.objects.filter(contact=self):
            attr = card.add("tel")
            attr.value = phone.number
            attr.type_param = phone.type
        return card.serialize()

    def update_from_vcard(self, content):
        """Update this contact according to given vcard."""
        vcard = vobject.readOne(content)
        self.uid = vcard.uid.value
        name = getattr(vcard, "n", None)
        if name:
            self.first_name = name.value.given
            self.last_name = name.value.family
        address = getattr(vcard, "adr", None)
        if address:
            self.address = address.value.street
            self.zipcode = address.value.code
            self.city = address.value.city
            self.state = address.value.region
            self.country = address.value.country
        birth_date = getattr(vcard, "bday", None)
        if birth_date:
            self.birth_date = parse(birth_date.value)
        for cfield, mfield in constants.CDAV_TO_MODEL_FIELDS_MAP.items():
            value = getattr(vcard, cfield, None)
            if value:
                if isinstance(value.value, list):
                    setattr(self, mfield, value.value[0])
                else:
                    setattr(self, mfield, value.value)
        self.save()
        email_list = getattr(vcard, "email_list", [])
        EmailAddress.objects.filter(contact=self).delete()
        to_create = []
        for email in email_list:
            addr = EmailAddress(contact=self, address=email.value.lower())
            if hasattr(email, "type_param"):
                addr.type = email.type_param.lower()
            to_create.append(addr)
        EmailAddress.objects.bulk_create(to_create)
        PhoneNumber.objects.filter(contact=self).delete()
        to_create = []
        phone_list = getattr(vcard, "tel_list", [])
        for tel in phone_list:
            pnum = PhoneNumber(contact=self, number=tel.value.lower())
            if hasattr(tel, "type_param"):
                pnum.type = tel.type_param.lower()
            to_create.append(pnum)
        PhoneNumber.objects.bulk_create(to_create)


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
