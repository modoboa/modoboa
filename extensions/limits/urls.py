from django.conf.urls.defaults import *

urlpatterns = patterns(
    'modoboa.extensions.limits.views',
    (r'reseller/edit/(?P<resid>\d+)/$', 'edit_reseller'),
    (r'pool/edit/(?P<resid>\d+)/$', 'edit_limits_pool'),
    )
