#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from django.conf import settings
from modoboa.admin.models import Domain, Mailbox

if __name__ == "__main__":
    if not "modoboa.extensions.postfix_autoreply" in settings.INSTALLED_APPS:
        print "Postfix autoreply extension is not activated"
        sys.exit(1)

    import modoboa.extensions.postfix_autoreply.main as par
    from modoboa.extensions.postfix_autoreply.models import Transport, Alias
        
    par.init()
    doms = Domain.objects.all()
    for dom in doms:
        try:
            trans = Transport.objects.get(domain="autoreply.%s" % dom.name)
            continue
        except Transport.DoesNotExist:
            par.onCreateDomain(dom=dom)
        mboxes = Mailbox.objects.filter(domain=dom.id)
        for mb in mboxes:
            try:
                alias = Alias.objects.get(full_address=mb.full_address)
                continue
            except Alias.DoesNotExist:
                par.onCreateMailbox(mbox=mb)

