# coding: utf-8
"""
Postfix auto-replies plugin.

This module provides a way to integrate Modoboa auto-reply
functionality into Postfix.

"""
from django.conf.urls.defaults import include
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_noop as _, ugettext
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from models import *

def infos():
    return {
        "name" : "Postfix autoreply",
        "version" : "1.0",
        "description" : ugettext("Auto-reply (vacation) functionality using Postfix"),
        "url" : "postfix_autoreply"
        }

def init():
    from modoboa.admin.models import Domain

    for dom in Domain.objects.all():
        try:
            trans = Transport.objects.get(domain="autoreply.%s" % dom.name)
        except Transport.DoesNotExist:
            onCreateDomain(None, dom)
        else:
            continue

        for mb in dom.mailbox_set.all():
            try:
                alias = Alias.objects.get(full_address=mb.full_address)
            except Alias.DoesNotExist:
                onCreateMailbox(None, mb)

def load():
    parameters.register_admin(
        "AUTOREPLIES_TIMEOUT", 
        type="int", deflt=86400,
        help=_("Timeout in seconds between two auto-replies to the same recipient")
        )

def destroy():
    events.unregister("CreateDomain", onCreateDomain)
    events.unregister("DeleteDomain", onDeleteDomain)
    events.unregister("CreateMailbox", onCreateMailbox)
    events.unregister("DeleteMailbox", onDeleteMailbox)
    events.unregister("ModifyMailbox", onModifyMailbox)
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("postfix_autoreply")

@events.observe("UserMenuDisplay")
def menu(target, user):
    import views

    if target != "uprefs_menu":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name" : "autoreply",
         "url" : reverse(views.autoreply),
         "label" : ugettext("Auto-reply message"),
         "modal": True,
         "modalcb" : "arform_cb"}
        ]

@events.observe("CreateDomain")
def onCreateDomain(user, domain):
    transport = Transport()
    transport.domain = "autoreply.%s" % domain.name
    transport.method = "autoreply:"
    transport.save()

@events.observe("DeleteDomain")
def onDeleteDomain(domain):
    trans = Transport.objects.get(domain="autoreply.%s" % domain.name)
    trans.delete()

@events.observe("CreateMailbox")
def onCreateMailbox(user, mailbox):
    alias = Alias()
    alias.full_address = mailbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()

@events.observe("DeleteMailbox")
def onDeleteMailbox(mailboxes):
    from modoboa.admin.models import Mailbox

    if isinstance(mailboxes, Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        try:
            alias = Alias.objects.get(full_address=mailbox.full_address)
        except Alias.DoesNotExist:
            pass
        else:
            alias.delete()

@events.observe("ModifyMailbox")
def onModifyMailbox(mailbox, oldmailbox):
    if oldmailbox.full_address == mailbox.full_address:
        return
    alias = Alias.objects.get(full_address=oldmailbox.full_address)
    alias.full_address = mailbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()

@events.observe("GetStaticContent")
def get_static_content():
    return """<script type="text/javascript">
function arform_cb() {
    $('#id_untildate').datepicker({format: 'yyyy-mm-dd'});
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            error_cb: arform_cb,
            formid: "arform"
        });
    });
}
</script>
"""
