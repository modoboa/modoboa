from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.extensions.sievefilters.views',
                       (r'^$', 'index'),
                       (r'^getscript/$', 'getscript'),
                       (r'^savescript/$', 'savescript'),
                       (r'^newfs/$', 'new_filters_set'),
                       (r'^deletefs/$', 'delete_filters_set'),
                       (r'^activatefs/$', 'activate_filters_set'),
                       )
