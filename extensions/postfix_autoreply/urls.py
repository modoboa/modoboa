from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.postfix_autoreply.views',
                       url(r'^$', 'autoreply'),
                       )
