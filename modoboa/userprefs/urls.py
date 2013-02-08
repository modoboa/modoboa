# coding: utf-8
from django.conf.urls.defaults import patterns, url
from modoboa.lib import events

urlpatterns = patterns('modoboa.userprefs.views',
                       url(r'^$', 'index'),
                       (r'^preferences/$', 'preferences'),
                       (r'^profile/$', 'profile'),
                       (r'^forward/$', 'forward'),
                       )

urlpatterns += patterns('',
                        *events.raiseQueryEvent("ExtraUprefsRoutes"))
