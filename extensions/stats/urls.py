from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.extensions.stats.views',
                       url(r'^$', 'adminindex', name='fullindex'),
                       url(r'^(?P<dom_id>\d+)/$', 'index', name='domindex'),
                       url(r'^graph/$', "getgraph", name="getgraph_root"),
                       url(r'^graph/(?P<dom_id>\w+)/$', "getgraph", name="getgraph"),
                       )


