"""Contacts serializers."""

from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import serializers

from . import models
from . import tasks


class AddressBookSerializer(serializers.ModelSerializer):
    """Address book serializer."""

    class Meta:
        model = models.AddressBook
        fields = ("pk", "name", "url", "last_sync")


class EmailAddressSerializer(serializers.ModelSerializer):
    """Email address serializer."""

    class Meta:
        model = models.EmailAddress
        fields = ("pk", "address", "type")


class EmailAddressWithNameSerializer(serializers.ModelSerializer):
    """Email address + contact name serializer."""

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = models.EmailAddress
        fields = ("pk", "address", "type", "display_name")

    def get_display_name(self, obj):
        """Return display name."""
        if obj.contact.display_name:
            return obj.contact.display_name
        return f"{obj.contact.first_name} {obj.contact.last_name}"


class PhoneNumberSerializer(serializers.ModelSerializer):
    """Phone number serializer."""

    class Meta:
        model = models.PhoneNumber
        fields = ("pk", "number", "type")


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""

    class Meta:
        model = models.Category
        fields = ("pk", "name")

    def create(self, validated_data):
        """Use current user."""
        user = self.context["request"].user
        return models.Category.objects.create(user=user, **validated_data)


class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer."""

    emails = EmailAddressSerializer(many=True)
    phone_numbers = PhoneNumberSerializer(many=True, required=False)

    class Meta:
        model = models.Contact
        fields = (
            "pk",
            "first_name",
            "last_name",
            "categories",
            "emails",
            "phone_numbers",
            "company",
            "position",
            "address",
            "zipcode",
            "city",
            "country",
            "state",
            "note",
            "birth_date",
            "display_name",
        )

    def validate(self, data):
        """Make sure display name or first/last names are set."""
        condition = (
            not data.get("first_name")
            and not data.get("last_name")
            and not data.get("display_name")
        )
        if not self.partial:
            if condition:
                msg = _("Name or display name required")
                raise serializers.ValidationError(
                    {"first_name": msg, "last_name": msg, "display_name": msg}
                )
            if not data.get("display_name"):
                data["display_name"] = data.get("first_name", "")
                if data["display_name"]:
                    data["display_name"] += " "
                data["display_name"] += data.get("last_name", "")
        return data

    def create(self, validated_data):
        """Use current user."""
        request = self.context["request"]
        addressbook = request.user.addressbook_set.first()
        categories = validated_data.pop("categories", [])
        emails = validated_data.pop("emails")
        phone_numbers = validated_data.pop("phone_numbers", [])
        contact = models.Contact.objects.create(
            addressbook=addressbook, **validated_data
        )
        to_create = []
        for email in emails:
            to_create.append(models.EmailAddress(contact=contact, **email))
        models.EmailAddress.objects.bulk_create(to_create)
        to_create = []
        for phone_number in phone_numbers:
            to_create.append(models.PhoneNumber(contact=contact, **phone_number))
        if to_create:
            models.PhoneNumber.objects.bulk_create(to_create)
        if categories:
            for category in categories:
                contact.categories.add(category)
        condition = addressbook.last_sync and addressbook.user.parameters.get_value(
            "enable_carddav_sync"
        )
        if condition:
            tasks.push_contact_to_cdav(request, contact)
        return contact

    def update_emails(self, instance, emails):
        """Update instance emails."""
        local_addresses = []
        local_objects = []
        for email in instance.emails.all():
            local_addresses.append(email.address)
            local_objects.append(email)
        to_create = []
        for email in emails:
            if email["address"] not in local_addresses:
                to_create.append(models.EmailAddress(contact=instance, **email))
                continue
            index = local_addresses.index(email["address"])
            local_email = local_objects[index]
            condition = (
                local_email.type != email["type"]
                or local_email.address != email["address"]
            )
            if condition:
                local_email.type = email["type"]
                local_email.address = email["address"]
                local_email.save()
            local_addresses.pop(index)
            local_objects.pop(index)
        models.EmailAddress.objects.filter(
            pk__in=[email.pk for email in local_objects]
        ).delete()
        models.EmailAddress.objects.bulk_create(to_create)

    def update_phone_numbers(self, instance, phone_numbers):
        """Update instance phone numbers."""
        local_phones = []
        local_objects = []
        for phone in instance.phone_numbers.all():
            local_phones.append(phone.number)
            local_objects.append(phone)
        to_create = []
        for phone in phone_numbers:
            if phone["number"] not in local_phones:
                to_create.append(models.PhoneNumber(contact=instance, **phone))
                continue
            index = local_phones.index(phone["number"])
            local_phone = local_objects[index]
            condition = (
                local_phone.type != phone["type"]
                or local_phone.number != phone["number"]
            )
            if condition:
                local_phone.type = phone["type"]
                local_phone.number = phone["number"]
                local_phone.save()
            local_phones.pop(index)
            local_objects.pop(index)
        instance.phone_numbers.filter(
            pk__in=[phone.pk for phone in local_objects]
        ).delete()
        models.PhoneNumber.objects.bulk_create(to_create)

    def update(self, instance, validated_data):
        """Update contact."""
        emails = validated_data.pop("emails", None)
        phone_numbers = validated_data.pop("phone_numbers", None)
        categories = validated_data.pop("categories", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.categories.set(categories)
        instance.save()

        if emails is not None:
            self.update_emails(instance, emails)
        if phone_numbers is not None:
            self.update_phone_numbers(instance, phone_numbers)

        condition = (
            instance.addressbook.last_sync
            and instance.addressbook.user.parameters.get_value("enable_carddav_sync")
        )
        if condition:
            tasks.update_contact_cdav(self.context["request"], instance)

        return instance


class UserPreferencesSerializer(serializers.Serializer):
    """Serializer to save user preferences."""

    enable_carddav_sync = serializers.BooleanField(default=False)
    sync_frequency = serializers.IntegerField(default=300)

    def validate_sync_frequency(self, value):
        """Make sure frequency is a positive integer."""
        if value < 60:
            raise serializers.ValidationError(_("Minimum allowed value is 60s"))
        return value

    def post_save(self, request):
        """Create remote cal if necessary."""
        if not self.validated_data["enable_carddav_sync"]:
            return
        abook = request.user.addressbook_set.first()
        if abook.last_sync:
            return
        tasks.create_cdav_addressbook(abook, request.auth)
        if not abook.contact_set.exists():
            abook.last_sync = timezone.now()
            abook.save(update_fields=["last_sync"])
