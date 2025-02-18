"""The sieve filters editor of Modoboa."""

from pkg_resources import get_distribution, DistributionNotFound


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

default_app_config = "modoboa_sievefilters.apps.SieveFiltersConfig"
