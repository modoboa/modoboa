"""Cache management."""

from datetime import datetime

from modoboa.lib.json_field_utils import json_to_datetime
from modoboa.lib.sysutils import guess_extension_name


class CacheManager:
    """A manager for cache."""

    def __init__(self, cache):
        """Constructor."""
        self._cache = cache

    def get_value(self, cache_label, app=None, raise_exception=True):
        """Return the value associated to the specified parameter."""
        if app is None:
            app = guess_extension_name()
        cache_entry = self.get_cache_entry(
            cache_label, app, raise_exception)
        if cache_entry is None:
            return None
        return cache_entry.get("value")

    def get_last_mod(self, cache_label, app=None, raise_exception=True):
        """Returns the last modification date for the specified parameter."""
        if app is None:
            app = guess_extension_name()
        cache_entry = self.get_cache_entry(
            cache_label, app, raise_exception)
        if cache_entry is None:
            return None
        return cache_entry.get("last_update")

    def get_cache_entry(self, cache_label, app=None, raise_exception=True):
        """Return the entry associated to the specified parameter."""
        if app is None:
            app = guess_extension_name()
        # Compat. with the old way...
        parameter = cache_label.lower()
        try:
            entry = self._cache[app][parameter]
            entry["last_update"] = json_to_datetime(entry["last_update"])
        except KeyError:
            if raise_exception:
                raise
            return None

        return entry

    def set_cache_entry(self, parameter, value, app=None):
        """Set parameter for the given app."""
        if app is None:
            app = guess_extension_name()
        if self._cache.get(app) is None:
            self._cache[app] = {}
        self._cache[app][parameter] = {
            "value": value,
            "last_update": datetime.utcnow()
            }
