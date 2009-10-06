from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.amavis_quarantine.main',
                       (r'^$', 'index'),
                       (r'^viewmail/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
                       (r'^viewheaders/(?P<mail_id>[\w\-\+]+)/$', 'viewheaders'),
                       (r'^process/$', 'process'),
                       (r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete'),
                       (r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release'),
                       (r'^search/', 'search'),
                       )
