"""Utilies for modoboa.rspamd plugin."""


def get_rspamd_options():
    from modoboa.core import models

    rspamd_options = {}
    localconfig = models.LocalConfig.objects.first()
    rspamd_location = localconfig.parameters.get_value(
        "rspamd_dashboard_location", raise_exception=False
    )
    if not rspamd_location:
        return None
    rspamd_options["location"] = rspamd_location
    return rspamd_options
