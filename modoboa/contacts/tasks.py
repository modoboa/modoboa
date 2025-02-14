"""Async tasks."""

from django.utils import timezone

from .lib import carddav
from . import models


def get_cdav_client(addressbook, user: str, passwd: str, write_support=False):
    """Instantiate a new CardDAV client."""
    return carddav.PyCardDAV(
        addressbook.url, user=user, passwd=passwd, write_support=write_support
    )


def get_cdav_client_from_request(request, addressbook, *args, **kwargs):
    """Create a connection from a Request object."""
    return get_cdav_client(
        addressbook,
        request.user.username,
        passwd=request.auth,
        **kwargs,
    )


def create_cdav_addressbook(addressbook, password):
    """Create CardDAV address book."""
    clt = carddav.PyCardDAV(
        addressbook.url,
        user=addressbook.user.username,
        passwd=password,
        write_support=True,
    )
    clt.create_abook()


def push_addressbook_to_carddav(request, addressbook):
    """Push every addressbook item to carddav collection.

    Use only once.
    """
    clt = get_cdav_client_from_request(request, addressbook, write_support=True)
    for contact in addressbook.contact_set.all():
        href, etag = clt.upload_new_card(contact.uid, contact.to_vcard())
        contact.etag = etag
        contact.save(update_fields=["etag"])
    addressbook.last_sync = timezone.now()
    addressbook.sync_token = clt.get_sync_token()
    addressbook.save(update_fields=["last_sync", "sync_token"])


def sync_addressbook_from_cdav(request, addressbook):
    """Fetch changes from CardDAV server."""
    clt = get_cdav_client_from_request(request, addressbook)
    changes = clt.sync_vcards(addressbook.sync_token)
    if not len(changes["cards"]):
        return
    for card in changes["cards"]:
        # UID sometimes embded .vcf extension, sometimes not...
        long_uid = card["href"].split("/")[-1]
        short_uid = long_uid.split(".")[0]
        if "200" in card["status"]:
            content = clt.get_vcard(card["href"]).decode()
            contact = models.Contact.objects.filter(
                uid__in=[long_uid, short_uid]
            ).first()
            if not contact:
                contact = models.Contact(addressbook=addressbook)
            if contact.etag != card["etag"]:
                contact.etag = card["etag"]
                contact.update_from_vcard(content)
        elif "404" in card["status"]:
            models.Contact.objects.filter(uid__in=[long_uid, short_uid]).delete()
    addressbook.last_sync = timezone.now()
    addressbook.sync_token = changes["token"]
    addressbook.save(update_fields=["last_sync", "sync_token"])


def push_contact_to_cdav(request, contact):
    """Upload new contact to cdav collection."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    path, etag = clt.upload_new_card(contact.uid, contact.to_vcard())
    contact.etag = etag
    contact.save(update_fields=["etag"])


def update_contact_cdav(request, contact):
    """Update existing contact."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    uid = contact.uid
    if not uid.endswith(".vcf"):
        uid += ".vcf"
    result = clt.update_vcard(contact.to_vcard(), uid, contact.etag)
    contact.etag = result["cards"][0]["etag"]
    contact.save(update_fields=["etag"])


def delete_contact_cdav(request, contact):
    """Delete a contact."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    uid = contact.uid
    if not uid.endswith(".vcf"):
        uid += ".vcf"
    clt.delete_vcard(uid, contact.etag)
