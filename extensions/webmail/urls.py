from django.conf.urls.defaults import *

#
# FIXME: there is a big issue with this url mapping. If a folder's
# name matches one of the first entries (from "compose" to
# "attachments"), the associated folder will not be accessible.
#
urlpatterns = patterns('modoboa.extensions.webmail.views',
                       #(r'^$', "index"),
                       (r'^$', "newindex"),
                       (r'^submailboxes', "submailboxes"),

#                       (r'^compose/$', "compose"),
                       (r'^move/$', "move"),
                       (r'^mark/(?P<name>.+)/$', "mark"),
                       (r'^empty/(?P<name>.+)/$', "empty"),
                       (r'^compact/(?P<name>.+)/$', "compact"),
                       (r'^newfolder/$', "newfolder"),
                       (r'^editfolder/$', 'editfolder'),
                       (r'^delfolder/$', 'delfolder'),

                       (r'^attachments/$', 'attachments'),
                       (r'^delattachment/$', 'delattachment'),

                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/part/$', 'getattachment'),
                       (r'^(?P<fdname>.+)/(?P<mail_id>[\w\-\+]+)/delete/$', 'delete'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/content/$', 'getmailcontent'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/forward/$', 'forward'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/reply/$', 'reply'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^(?P<name>.+)/$', "folder"),
                       )
