from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.extensions.postfix_autoreply.models import Transport, Alias


@events.observe("ExtraUprefsJS")
def extra_js(user):
    return ["""function autoreply_cb() {
    $('#id_untildate').datepicker({format: 'yyyy-mm-dd', language: '%s'});
}
""" % parameters.get_user(user, "LANG", app="core")
    ]


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "uprefs_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "autoreply",
         "class": "ajaxlink",
         "url": "autoreply/",
         "label": ugettext_lazy("Auto-reply message")}
    ]


@events.observe("DomainCreated")
def onDomainCreated(user, domain):
    transport = Transport()
    transport.domain = "autoreply.%s" % domain.name
    transport.method = "autoreply:"
    transport.save()


@events.observe("DomainModified")
def onDomainModified(domain):
    if domain.oldname == domain.name:
        return
    Transport.objects.filter(domain="autoreply.%s" % domain.oldname) \
        .update(domain="autoreply.%s" % domain.name)
    for al in Alias.objects.filter(full_address__contains="@%s" % domain.oldname):
        new_address = al.full_address.replace("@%s" % domain.oldname, "@%s" % domain.name)
        al.full_address = new_address
        al.autoreply_address = "%s@autoreply.%s" % (new_address, domain.name)
        al.save()


@events.observe("DomainDeleted")
def onDomainDeleted(domain):
    Transport.objects.filter(domain="autoreply.%s" % domain.name).delete()


@events.observe("MailboxCreated")
def onMailboxCreated(user, mailbox):
    alias = Alias()
    alias.full_address = mailbox.full_address
    alias.autoreply_address = \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()


@events.observe("MailboxDeleted")
def onMailboxDeleted(mailboxes):
    from modoboa.extensions.admin.models import Mailbox

    if isinstance(mailboxes, Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        try:
            alias = Alias.objects.get(full_address=mailbox.full_address)
        except Alias.DoesNotExist:
            pass
        else:
            alias.delete()


@events.observe("MailboxModified")
def onModifyMailbox(mailbox, oldmailbox):
    if oldmailbox.full_address == mailbox.full_address:
        return
    alias = Alias.objects.get(full_address=oldmailbox.full_address)
    alias.full_address = mailbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()
