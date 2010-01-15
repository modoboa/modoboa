from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       (r'^$', "index"),
                       url(r'^viewmail/(?P<mail_id>[\w\-\+]+)/$', 'viewmail', 
                           name="viewmail_std"),
                       url(r'^viewmail/$', 'viewmail', name="viewmail_null"),
                       (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
#                       (r'^(?P<folder>.+)/$', "folder"),
                       )
