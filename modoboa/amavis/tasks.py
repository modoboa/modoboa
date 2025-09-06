"""Async tasks."""

# from django.utils.translation import ngettext

from modoboa.core import models as core_models

from .lib import SpamassassinClient
from .sql_connector import SQLconnector


def manual_learning(user_pk: int, mtype: str, selection: list[dict], recipient_db: str):
    """Task to trigger manual learning for given selection."""
    user = core_models.User.objects.get(pk=user_pk)
    connector = SQLconnector()
    saclient = SpamassassinClient(user, recipient_db)
    for item in selection:
        content = connector.get_mail_content(item["mailid"].encode("ascii"))
        result = (
            saclient.learn_spam(item["rcpt"], content)
            if mtype == "spam"
            else saclient.learn_ham(item["rcpt"], content)
        )
        if not result:
            break
        connector.set_msgrcpt_status(item["rcpt"], item["mailid"], mtype[0].upper())
    if saclient.error is None:
        saclient.done()

    #     message = ngettext("%(count)d message processed successfully",
    #                        "%(count)d messages processed successfully",
    #                        len(selection)) % {"count": len(selection)}
    # else:
    #     message = saclient.error
