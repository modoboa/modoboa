from django.conf.urls.defaults import *

urlpatterns = patterns(
    'modoboa.extensions.limits.views',
    (r'^$', 'resellers'),
    (r'reseller/new/$', 'new_reseller'),
    (r'reseller/edit/(?P<resid>\d+)/$', 'edit_reseller'),
    (r'reseller/delete/$', 'delete_resellers'),
    (r'pool/edit/(?P<resid>\d+)/$', 'edit_limits_pool'),
    )
