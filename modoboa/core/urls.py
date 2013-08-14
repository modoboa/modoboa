from django.conf.urls import patterns, url


urlpatterns = patterns(
    'modoboa.core.views',
    
    (r'^settings/$', 'viewsettings'),
    (r'^settings/parameters/$', 'viewparameters'),
    (r'^settings/parameters/save/$', 'saveparameters'),
    (r'^settings/extensions/$', 'viewextensions'),
    (r'^settings/extensions/save/$', 'saveextensions'),
    (r'^settings/info/$', 'information'),
    (r'^settings/logs/$', 'logs'),
)
