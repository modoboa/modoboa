#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from mailng.admin.models import Domain, Mailbox

if __name__ == "__main__":
    if "mailng.extensions.postfix_autoreply" in settings.INSTALLED_APPS:
        import mailng.extensions.postfix_autoreply.main as par
        from mailng.extensions.postfix_autoreply.models import Transport, Alias
        
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

