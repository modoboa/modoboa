"""Contacts API urls."""

from rest_framework import routers

from modoboa.contacts import viewsets


router = routers.SimpleRouter()
router.register(r"address-books", viewsets.AddressBookViewSet, basename="addressbook")
router.register(r"categories", viewsets.CategoryViewSet, basename="category")
router.register(r"contacts", viewsets.ContactViewSet, basename="contact")
router.register(r"emails", viewsets.EmailAddressViewSet, basename="emailaddress")

urlpatterns = router.urls
