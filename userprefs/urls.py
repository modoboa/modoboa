from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.userprefs.views',
                       url(r'^$', 'index'),
                       (r'^preferences/$', 'preferences'),
                       (r'^profile/$', 'profile'),
                       (r'^forward/$', 'forward'),
                       )
