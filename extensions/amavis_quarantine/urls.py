from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.amavis_quarantine.main',
                       (r'^$', 'index'),
                       (r'^viewmail/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^viewheaders/(?P<mail_id>[\w\-\+]+)/$', 'viewheaders'),
                       (r'^process/$', 'process')
                       )
