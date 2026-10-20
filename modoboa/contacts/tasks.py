"""Async tasks."""

import contextlib
import logging
from urllib.parse import unquote

import requests
import vobject

from django.db import OperationalError
from django.db.models import Q
from django.utils import timezone

from modoboa.lib.oauth2 import get_access_token

from .lib import carddav
from . import constants
from . import models

logger = logging.getLogger("modoboa.contacts")


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
        passwd=get_access_token(request),
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


@contextlib.contextmanager
def sync_lock(addressbook_id: int):
    """Atomic lock: only one sync at a time per address book.

    The lock expires after SYNC_LOCK_TIMEOUT in case the worker was killed.
    Yield False if a sync is already running.
    """
    now = timezone.now()
    locked = (
        models.AddressBook.objects.filter(pk=addressbook_id)
        .filter(
            Q(sync_started=None) | Q(sync_started__lt=now - constants.SYNC_LOCK_TIMEOUT)
        )
        .update(sync_started=now)
    )
    try:
        yield bool(locked)
    finally:
        if locked:
            # Don't release a lock taken by another sync after ours expired
            models.AddressBook.objects.filter(
                pk=addressbook_id, sync_started=now
            ).update(sync_started=None)


def push_addressbook_to_carddav(addressbook_id: int, access_token: str):
    """Push every addressbook item to carddav collection.

    Use only once. Contacts already pushed by an interrupted run (they
    have an etag) are skipped.
    """
    with sync_lock(addressbook_id) as locked:
        if not locked:
            return
        addressbook = models.AddressBook.objects.get(pk=addressbook_id)
        if addressbook.last_sync:
            return
        clt = get_cdav_client(
            addressbook, addressbook.user.username, access_token, write_support=True
        )
        for contact in addressbook.contact_set.filter(etag=""):
            href, etag = clt.upload_new_card(contact.filename, contact.to_vcard())
            contact.etag = etag
            contact.save(update_fields=["etag"])
        addressbook.last_sync = timezone.now()
        addressbook.sync_token = clt.get_sync_token()
        addressbook.save(update_fields=["last_sync", "sync_token"])


def sync_card(clt, addressbook, card: dict, filename: str):
    """Apply a change reported by the CardDAV server."""
    contacts = addressbook.contact_set.filter(filename=filename)
    if "404" in card["status"]:
        contacts.delete()
        return
    if "200" not in card["status"]:
        return
    contact = contacts.first()
    if contact and contact.etag == card["etag"]:
        return
    vcard = vobject.readOne(clt.get_vcard(card["href"]).decode())
    if not contact and hasattr(vcard, "uid"):
        # Contacts synced before filenames were stored
        contact = addressbook.contact_set.filter(uid=vcard.uid.value).first()
    if not contact:
        contact = models.Contact(addressbook=addressbook)
    contact.etag = card["etag"]
    contact.filename = filename
    contact.update_from_vcard(vcard)


def sync_addressbook_from_cdav(addressbook_id: int, access_token: str):
    """Fetch changes from CardDAV server."""
    with sync_lock(addressbook_id) as locked:
        if not locked:
            return
        addressbook = models.AddressBook.objects.get(pk=addressbook_id)
        clt = get_cdav_client(addressbook, addressbook.user.email, access_token)
        full_sync = not addressbook.sync_token
        try:
            changes = clt.sync_vcards(addressbook.sync_token)
        except requests.HTTPError as err:
            # Token refused by the server (RFC 6578 valid-sync-token)
            if full_sync or err.response.status_code not in (403, 409):
                raise
            full_sync = True
            changes = clt.sync_vcards("")
        if not len(changes["cards"]) and not full_sync:
            return
        remote_filenames = set()
        for card in changes["cards"]:
            filename = unquote(card["href"].rstrip("/").split("/")[-1])
            if "200" in card.get("status", ""):
                remote_filenames.add(filename)
            try:
                sync_card(clt, addressbook, card, filename)
            except (requests.RequestException, OperationalError):
                # Server or database unavailable: retry the whole sync later
                raise
            except Exception:
                # A single bad card must not block the sync forever
                logger.exception(
                    "Failed to sync card %s of address book %s",
                    card["href"],
                    addressbook.pk,
                )
        if full_sync:
            # Pushed contacts missing from the server were deleted remotely
            addressbook.contact_set.exclude(etag="").exclude(
                filename__in=remote_filenames
            ).delete()
        addressbook.last_sync = timezone.now()
        addressbook.sync_token = changes["token"]
        addressbook.save(update_fields=["last_sync", "sync_token"])


def push_contact_to_cdav(request, contact):
    """Upload new contact to cdav collection."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    path, etag = clt.upload_new_card(contact.filename, contact.to_vcard())
    contact.etag = etag
    contact.save(update_fields=["etag"])


def update_contact_cdav(request, contact):
    """Update existing contact."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    result = clt.update_vcard(contact.to_vcard(), contact.filename, contact.etag)
    contact.etag = result["cards"][0]["etag"]
    contact.save(update_fields=["etag"])


def delete_contact_cdav(request, contact):
    """Delete a contact."""
    clt = get_cdav_client_from_request(request, contact.addressbook, write_support=True)
    clt.delete_vcard(contact.filename, contact.etag)
