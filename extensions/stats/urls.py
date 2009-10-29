from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.stats.main',
                       (r'^$', 'index'),
                       (r'^index.html$', 'index'),
                       (r'^display/(?P<dom_id>\d+)/(?P<graph_t>\w+)/$', 'graph_display'),
                       (r'^domain/(?P<dom_id>\d+)/$', 'domain'),
                       )


