"""Core views."""

from .base import RootDispatchView
from .dashboard import DashboardView

__all__ = [
    "DashboardView",
    "RootDispatchView",
]
