"""Core Jobs"""


def clean_log():
    import datetime

    from modoboa.core.models import Log
    from modoboa.parameters import tools as param_tools

    from django.utils import timezone

    log_maximum_age = param_tools.get_global_parameter("log_maximum_age")
    limit = timezone.now() - datetime.timedelta(log_maximum_age)
    Log.objects.filter(date_created__lt=limit).delete()
