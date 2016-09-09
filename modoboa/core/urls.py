"""Core urls."""

from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',

    url(r'^$', views.RootDispatchView.as_view(), name="root"),
    url(r'^dashboard/$', views.DashboardView.as_view(), name="dashboard"),

    url(r'^accounts/login/$', 'modoboa.core.views.auth.dologin',
        name="login"),
    url(r'^accounts/logout/$', 'modoboa.core.views.auth.dologout',
        name="logout"),

    url(r'^core/$', 'modoboa.core.views.admin.viewsettings',
        name="index"),
    url(r'^core/parameters/$', 'modoboa.core.views.admin.viewparameters',
        name="parameter_listl"),
    url(r'^core/parameters/save/$', 'modoboa.core.views.admin.saveparameters',
        name="parameter_save"),
    url(r'^core/info/$', 'modoboa.core.views.admin.information',
        name="information"),
    url(r'^core/logs/$', 'modoboa.core.views.admin.logs', name="log_list"),
    url(r'^core/logs/page/$', 'modoboa.core.views.admin.logs_page',
        name="logs_page"),
    url(r'^core/top_notifications/check/$',
        'modoboa.core.views.admin.check_top_notifications',
        name='top_notifications_check'),

    url(r'^user/$', 'modoboa.core.views.user.index', name="user_index"),
    url(r'^user/preferences/$', 'modoboa.core.views.user.preferences',
        name="user_preferences"),
    url(r'^user/profile/$', 'modoboa.core.views.user.profile',
        name="user_profile"),
    url(r'^user/api/$', 'modoboa.core.views.user.api_access',
        name="user_api_access"),
)
