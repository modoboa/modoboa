from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       url(r'^$', "folder", name="index"),
                       (r'^compose/$', "compose"),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/content/$', 'getmailcontent'),
                       (r'^(?P<folder>.+)/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       url(r'^(?P<name>.+)/$', "folder", name="folder"),
                       )
