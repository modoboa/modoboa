from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.extensions.stats.views',
                       url(r'^$', 'index', name='fullindex'),
                       url(r'^graphs/$', "graphs"),
                       )


