from django.conf.urls import url, patterns

urlpatterns = patterns(
    'modoboa.extensions.radicale.views',

    url(r'^$', 'index', name="index"),
    url(r'^list/$', 'calendars_page', name="calendars_page"),
    url(r'^user/$', 'new_user_calendar', name='user_calendar_add'),
    url(r'^user/(?P<pk>\d+)/$', 'user_calendar',
        name='user_calendar'),
    url(r'^shared/$', 'new_shared_calendar',
        name='shared_calendar_add'),
    url(r'^shared/(?P<pk>\d+)/$', 'shared_calendar',
        name='shared_calendar'),
    url(r'^usernames/$', 'username_list', name='username_list'),
)
