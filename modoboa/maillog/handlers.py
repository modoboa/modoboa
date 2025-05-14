"""Modoboa stats signal handlers."""

from django.dispatch import receiver

from modoboa.parameters import tools as param_tools

from . import graphics
from . import signals


@receiver(signals.get_graph_sets)
def get_default_graphic_sets(sender, **kwargs):
    """Return graphic set."""
    mail_traffic_gset = graphics.MailTraffic(
        param_tools.get_global_parameter("greylist", raise_exception=False)
    )
    result = {mail_traffic_gset.html_id: mail_traffic_gset}
    if kwargs.get("user").is_superuser:
        account_gset = graphics.AccountGraphicSet()
        result.update({account_gset.html_id: account_gset})
    return result
