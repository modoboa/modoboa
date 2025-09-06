"""Core API urls."""

from django.urls import path

from rest_framework import routers

from . import views
from . import viewsets


router = routers.SimpleRouter()
router.register(r"account", viewsets.AccountViewSet, basename="account")
router.register(r"languages", viewsets.LanguageViewSet, basename="language")
router.register(r"logs/audit-trail", viewsets.LogViewSet)
router.register(r"fido", viewsets.FIDOViewSet, basename="fido")

urlpatterns = router.urls
urlpatterns += [
    path(
        "password_reset/",
        views.DefaultPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "reset_confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm_v2",
    ),
    path("sms_totp/", views.PasswordResetSmsTOTP.as_view(), name="sms_totp"),
    path(
        "admin/components/",
        views.ComponentsInformationAPIView.as_view(),
        name="components_information",
    ),
    path(
        "admin/news_feed/",
        views.NewsFeedAPIView.as_view(),
        name="news-feed",
    ),
    path(
        "admin/statistics/",
        views.StatisticsAPIView.as_view(),
        name="statistics",
    ),
    path("capabilities/", views.CapabilitiesAPIView.as_view(), name="capabilities"),
    path(
        "notifications/",
        views.NotificationsAPIView.as_view(),
        name="notifications",
    ),
    path("theme/", views.ThemeAPIView.as_view(), name="theme"),
]
