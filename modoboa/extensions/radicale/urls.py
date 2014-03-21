from django.conf.urls import patterns

urlpatterns = patterns(
    'modoboa.extensions.radicale.views',
    (r'^$', 'index'),
)
