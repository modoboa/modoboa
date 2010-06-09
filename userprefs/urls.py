from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.userprefs.views',
                       url(r'^$', 'index'),
                       (r'^preferences/$', 'preferences'),
                       (r'^preferences/save/$', 'savepreferences'),
                       (r'^changepassword/$', 'changepassword'),
                       (r'^confirm/$', 'confirm'),
                       )
