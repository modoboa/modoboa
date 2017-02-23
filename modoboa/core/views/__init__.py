"""Core views."""

from .admin import (
    check_top_notifications, information, logs, logs_page, parameters,
    viewsettings)
from .auth import dologin, dologout
from .base import RootDispatchView
from .dashboard import DashboardView
from .user import api_access, index, preferences, profile

__all__ = [
    "DashboardView",
    "RootDispatchView",
    "api_access",
    "check_top_notifications",
    "dologin",
    "dologout",
    "index",
    "information",
    "logs",
    "logs_page",
    "parameters",
    "preferences",
    "profile",
    "viewsettings",
]
