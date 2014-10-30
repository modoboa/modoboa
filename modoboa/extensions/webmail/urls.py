# coding: utf-8
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.extensions.webmail.views',

    url(r'^$', "index", name="index"),
    url(r'^submailboxes', "submailboxes", name="submailboxes_get"),
    url(r'^getmailcontent', 'getmailcontent', name="mailcontent_get"),
    url(r'^unseenmsgs', 'check_unseen_messages', name="unseen_messages_check"),

    url(r'^delete/$', 'delete', name="mail_delete"),
    url(r'^move/$', "move", name="mail_move"),
    url(r'^mark/(?P<name>.+)/$', "mark", name="mail_mark"),

    url(r'^newfolder/$', "newfolder", name="folder_add"),
    url(r'^editfolder/$', "editfolder", name="folder_change"),
    url(r'^delfolder/$', "delfolder", name="folder_delete"),
    url(r'^compressfolder/$', "folder_compress", name="folder_compress"),
    url(r'^emptytrash/$', "empty", name="trash_empty"),

    url(r'^attachments/$', 'attachments', name="attachment_list"),
    url(r'^delattachment/$', 'delattachment', name="attachment_delete"),
    url(r'^getattachment/$', 'getattachment', name="attachment_get"),
)
