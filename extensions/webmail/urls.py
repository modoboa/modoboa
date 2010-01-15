from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.webmail.main',
                       (r'^$', "index"),
                       (r'^(?P<folder>.+)/$', "folder"),
                       )
