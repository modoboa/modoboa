from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.demo.views',
                       (r'^sendvirus/$', 'send_virus'),
                       (r'^sendspam/$', 'send_spam'),
                       )
