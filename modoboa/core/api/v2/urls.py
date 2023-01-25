"""Core API urls."""

from django.urls import path

from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from . import views
from . import viewsets


router = routers.SimpleRouter()
router.register(r"account", viewsets.AccountViewSet, basename="account")
router.register(r"languages", viewsets.LanguageViewSet, basename="language")
router.register(r"logs/audit-trail", viewsets.LogViewSet)

urlpatterns = router.urls
urlpatterns += [
    path('token/', views.TokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path('token/refresh/', TokenRefreshView.as_view(),
         name="token_refresh"),
    path('password_reset/', views.DefaultPasswordResetView.as_view(),
         name="password_reset"),
    path('reset_confirm/', views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm_v2"),
    path('sms_totp/', views.PasswordResetSmsTOTP.as_view(),
         name="sms_totp"),
    path('admin/components/', views.ComponentsInformationAPIView.as_view(),
         name="components_information"),
]
