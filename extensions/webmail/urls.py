from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       (r'^$', "index"),
                       (r'^compose/$', "compose"),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/content/$', 'getmailcontent'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^(?P<name>.+)/$', "folder"),
                       )
