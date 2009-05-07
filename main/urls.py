from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.main.views',
                       url(r'^$', 'index'),
                       url(r'^autoreply/$', 'autoreply')
                       )
