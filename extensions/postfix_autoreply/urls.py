from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.extensions.postfix_autoreply.main',
                       url(r'^$', 'autoreply'),
                       )
