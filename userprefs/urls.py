from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.userprefs.views',
                       url(r'^$', 'index'),
                       url(r'^autoreply/$', 'autoreply'),
                       (r'^changepassword/$', 'changepassword'),
                       (r'^confirm/$', 'confirm'),
                       )
