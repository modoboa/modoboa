"""Radicale urls."""

from rest_framework_nested import routers

from . import viewsets

router = routers.SimpleRouter()
router.register(
    r"user-calendars", viewsets.UserCalendarViewSet, basename="user-calendar"
)
router.register(
    r"shared-calendars", viewsets.SharedCalendarViewSet, basename="shared-calendar"
)
router.register(r"attendees", viewsets.AttendeeViewSet, basename="attendee")
router.register(r"mailboxes", viewsets.MailboxViewSet, basename="mailbox")

calendars_router = routers.NestedSimpleRouter(
    router, r"user-calendars", lookup="calendar"
)
calendars_router.register(r"events", viewsets.UserEventViewSet, basename="user-event")
calendars_router.register(
    r"accessrules", viewsets.AccessRuleViewSet, basename="access-rule"
)
shared_calendars_router = routers.NestedSimpleRouter(
    router, r"shared-calendars", lookup="calendar"
)
shared_calendars_router.register(
    r"events", viewsets.SharedEventViewSet, basename="shared-event"
)

urlpatterns = router.urls + calendars_router.urls + shared_calendars_router.urls
