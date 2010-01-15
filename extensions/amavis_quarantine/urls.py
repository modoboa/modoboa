from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.amavis_quarantine.main',
                       (r'^$', 'index'),
                       url(r'^viewmail/(?P<mail_id>[\w\-\+]+)/$', 'viewmail', 
                           name="viewmail_std"),
                       url(r'^viewmail/$', 'viewmail', name="viewmail_null"),
                       (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
                       (r'^viewheaders/(?P<mail_id>[\w\-\+]+)/$', 'viewheaders'),
                       (r'^process/$', 'process'),
                       (r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete'),
                       (r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release'),
                       (r'^search/', 'search'),
                       )
