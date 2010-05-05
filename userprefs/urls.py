from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.userprefs.views',
                       url(r'^$', 'index'),
                       (r'^changepassword/$', 'changepassword'),
                       (r'^confirm/$', 'confirm'),
                       )
