from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       (r'^$', "index"),
                       (r'^compose/$', "compose"),
                       (r'^move/$', "move"),
                       (r'^mark/(?P<name>.+)/$', "mark"),
                       (r'^empty/(?P<name>.+)/$', "empty"),
                       (r'^compact/(?P<name>.+)/$', "compact"),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/part/$', 'getattachment'),
                       (r'^(?P<fdname>.+)/(?P<mail_id>[\w\-\+]+)/delete/$', 'delete'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/content/$', 'getmailcontent'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/forward/$', 'forward'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/reply/$', 'reply'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^(?P<name>.+)/$', "folder"),
                       )
