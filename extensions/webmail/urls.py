from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       (r'^$', "index"),
                       (r'^compose/$', "compose"),
                       (r'^move/$', "move"),
                       (r'^empty/(?P<name>.+)/', "empty"),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/content/$', 'getmailcontent'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/reply/$', 'reply'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^(?P<name>.+)/$', "folder"),
                       )
