from django.utils import timezone
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.extensions.postfix_autoreply.models import Transport, Alias
from .models import ARmessage


@events.observe("ExtraUprefsJS")
def extra_js(user):
    return ["""function autoreply_cb() {
    $('.datefield').datetimepicker({
        format: 'YYYY-MM-DD HH:mm:ss',
        language: '%(lang)s'
    });
}
""" % {'lang': parameters.get_user(user, "LANG", app="core")}
    ]


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "uprefs_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "autoreply",
         "class": "ajaxnav",
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
def onMailboxModified(mailbox):
    if not hasattr(mailbox, 'old_full_address'):
        return
    if mailbox.full_address == mailbox.old_full_address:
        return
    alias = Alias.objects.get(full_address=mailbox.old_full_address)
    alias.full_address = mailbox.full_address
    alias.autoreply_address =  \
        "%s@autoreply.%s" % (mailbox.full_address, mailbox.domain.name)
    alias.save()


@events.observe("ExtraFormFields")
def extra_mailform_fields(form_name, mailbox=None):
    """Define extra fields to include in mail forms.

    For now, only the auto-reply state can be modified.

    :param str form_name: form name (must be 'mailform')
    :param Mailbox mailbox: mailbox
    """
    from modoboa.lib.formutils import YesNoField

    if form_name != "mailform":
        return []
    status = False
    if mailbox is not None and mailbox.armessage_set.count():
        status = mailbox.armessage_set.all()[0].enabled
    return [
        ('autoreply', YesNoField(
            label=ugettext_lazy("Enable auto-reply"),
            initial="yes" if status else "no",
            help_text=ugettext_lazy("Enable or disable Postfix auto-reply")
        ))
    ]


@events.observe("SaveExtraFormFields")
def save_extra_mailform_fields(form_name, mailbox, values):
    """Set the auto-reply status for a mailbox.

    If a corresponding auto-reply message exists, we update its
    status. Otherwise, we create a message using default values.

    :param str form_name: form name (must be 'mailform')
    :param Mailbox mailbox: mailbox
    :param dict values: form values
    """
    if form_name != 'mailform':
        return
    if mailbox.armessage_set.count():
        arm = mailbox.armessage_set.all()[0]
    else:
        arm = ARmessage(mbox=mailbox)
        arm.subject = parameters.get_admin("DEFAULT_SUBJECT")
        arm.content = parameters.get_admin("DEFAULT_CONTENT") \
            % {'name': mailbox.user.fullname}
        arm.fromdate = timezone.now()
    arm.enabled = True if values['autoreply'] == 'yes' else False
    arm.save()
