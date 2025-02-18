"""Contacts factories."""

import factory

from modoboa.admin import factories as admin_factories

from . import models


class AddressBookFactory(factory.django.DjangoModelFactory):
    """Address book factory."""

    class Meta:
        model = models.AddressBook

    user = factory.SubFactory(admin_factories.UserFactory)
    name = "Contacts"
    _path = "contacts"


class CategoryFactory(factory.django.DjangoModelFactory):
    """Category factory."""

    class Meta:
        model = models.Category


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """Email address factory."""

    class Meta:
        model = models.EmailAddress

    type = "home"


class PhoneNumberFactory(factory.django.DjangoModelFactory):
    """Phone number factory."""

    class Meta:
        model = models.PhoneNumber

    type = "home"


class ContactFactory(factory.django.DjangoModelFactory):
    """Contact factory."""

    class Meta:
        model = models.Contact

    first_name = "Homer"
    last_name = "Simpson"
    display_name = factory.LazyAttribute(lambda c: f"{c.first_name}{c.last_name}")

    @factory.post_generation
    def categories(self, create, extracted, **dummy_kwargs):
        """Add categories to contact."""
        if not create or not extracted:
            return
        for item in extracted:
            self.categories.add(item)

    @factory.post_generation
    def emails(self, create, extracted, **dummy_kwargs):
        """Add emails to contact."""
        if not create or not extracted:
            return
        for item in extracted:
            EmailAddressFactory(contact=self, address=item)

    @factory.post_generation
    def phone_numbers(self, create, extracted, **dummy_kwargs):
        """Add phone numbers to contact."""
        if not create or not extracted:
            return
        for item in extracted:
            PhoneNumberFactory(contact=self, number=item)
