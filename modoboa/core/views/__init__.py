"""Core views."""

from .admin import (
    check_top_notifications, information, logs, logs_page, parameters,
    viewsettings
)
from .auth import (
    PasswordResetView, dologin, dologout, VerifySMSCodeView,
    ResendSMSCodeView, TwoFactorCodeVerifyView
)
from .base import RootDispatchView
from .dashboard import DashboardView
from .user import (
    api_access, index, preferences, profile, security)

__all__ = [
    "DashboardView",
    "PasswordResetView",
    "ResendSMSCodeView",
    "RootDispatchView",
    "VerifySMSCodeView",
    "api_access",
    "check_top_notifications",
    "dologin",
    "dologout",
    "TwoFactorCodeVerifyView",
    "index",
    "information",
    "logs",
    "logs_page",
    "parameters",
    "preferences",
    "profile",
    "viewsettings",
    "security"
]
