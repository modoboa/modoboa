"""Core views."""

from .admin import (
    check_top_notifications,
    information,
    logs,
    logs_page,
    parameters,
    viewsettings,
)
from .auth import (
    PasswordResetView,
    LoginView,
    dologout,
    VerifySMSCodeView,
    ResendSMSCodeView,
    TwoFactorCodeVerifyView,
    FidoAuthenticationBeginView,
    FidoAuthenticationEndView,
)
from .base import RootDispatchView
from .dashboard import DashboardView
from .user import api_access, index, preferences, profile, security

__all__ = [
    "DashboardView",
    "LoginView",
    "PasswordResetView",
    "ResendSMSCodeView",
    "RootDispatchView",
    "VerifySMSCodeView",
    "api_access",
    "check_top_notifications",
    "dologout",
    "TwoFactorCodeVerifyView",
    "FidoAuthenticationBeginView",
    "FidoAuthenticationEndView",
    "index",
    "information",
    "logs",
    "logs_page",
    "parameters",
    "preferences",
    "profile",
    "viewsettings",
    "security",
]
