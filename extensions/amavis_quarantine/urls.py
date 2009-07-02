from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.amavis_quarantine.main',
                       (r'^$', 'index'),
                       (r'^view/(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
                       (r'^process/$', 'process')
                       )
