from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.userprefs.views',
                       url(r'^$', 'index'),
                       (r'^preferences/$', 'preferences'),
                       (r'^preferences/save/$', 'savepreferences'),
                       (r'^changepassword/$', 'changepassword'),
                       )
