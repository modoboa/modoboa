"""Core urls."""

from django.urls import path
from django.views.generic.base import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/logout/", views.dologout, name="logout"),
    path(
        "accounts/2fa_verify/",
        views.TwoFactorCodeVerifyView.as_view(),
        name="2fa_verify",
    ),
    path(
        "accounts/fido/authenticate/begin",
        views.FidoAuthenticationBeginView.as_view(),
        name="fido_auth_begin",
    ),
    path(
        "accounts/fido/authenticate/end",
        views.FidoAuthenticationEndView.as_view(),
        name="fido_auth_end",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="core/robots.txt", content_type="text/plain"
        ),
    ),
]
