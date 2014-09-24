from django.conf.urls import url, patterns

urlpatterns = patterns(
    'modoboa.extensions.radicale.views',

    url(r'^$', 'index', name="index"),
    url(r'^calendars/$', 'calendars', name="calendar_list"),
    url(r'^usercalendar/$', 'new_user_calendar', name='user_calendar_add'),
    url(r'^usercalendar/(?P<pk>\d+)/$', 'user_calendar',
        name='user_calendar'),
    url(r'^sharedcalendar/$', 'new_shared_calendar',
        name='shared_calendar_add'),
    url(r'^sharedcalendar/(?P<pk>\d+)/$', 'shared_calendar',
        name='shared_calendar'),
    url(r'^usernames/$', 'username_list', name='username_list'),
)
