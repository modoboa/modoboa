from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.amavis_quarantine.main',
                       (r'^$', 'index'),
                       )
