from django.conf.urls import url, patterns

urlpatterns = patterns(
    'modoboa.extensions.radicale.views',
    (r'^$', 'index'),
    (r'^calendars/$', 'calendars'),
    url(r'^calendar/$', 'new_calendar', name='new_calendar'),
)
