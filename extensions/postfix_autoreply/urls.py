from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.extensions.postfix_autoreply.views',
                       url(r'^$', 'autoreply'),
                       )
