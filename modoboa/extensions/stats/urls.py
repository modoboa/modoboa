from django.conf.urls import patterns, include, url

urlpatterns = patterns('modoboa.extensions.stats.views',
                       url(r'^$', 'index', name='fullindex'),
                       url(r'^graphs/$', "graphs"),
                       )


