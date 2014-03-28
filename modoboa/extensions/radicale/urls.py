from django.conf.urls import url, patterns

urlpatterns = patterns(
    'modoboa.extensions.radicale.views',
    (r'^$', 'index'),
    (r'^calendars/$', 'calendars'),
    url(r'^usercalendar/$', 'new_user_calendar', name='new_user_calendar'),
    url(r'^usercalendar/(?P<pk>\d+)/$', 'user_calendar', name='user_calendar'),
    url(r'^sharedcalendar/$', 'new_shared_calendar',
        name='new_shared_calendar'),
    url(r'^sharedcalendar/(?P<pk>\d+)/$', 'shared_calendar',
        name='shared_calendar'),
)
