from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.extensions.stats.views',
                       url(r'^$', 'index', name='fullindex'),
                       url(r'^graph/$', "getgraph", name="getgraph_root"),
                       url(r'^graph/(?P<dom_id>\w+)/$', "getgraph", name="getgraph"),
                       )


