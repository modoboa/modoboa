from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',

    (r'^accounts/login/$', 'modoboa.core.views.auth.dologin'),
    (r'^accounts/logout/$', 'modoboa.core.views.auth.dologout'),

    (r'^core/$', 'modoboa.core.views.admin.viewsettings'),
    (r'^core/parameters/$', 'modoboa.core.views.admin.viewparameters'),
    (r'^core/parameters/save/$', 'modoboa.core.views.admin.saveparameters'),
    (r'^core/extensions/$', 'modoboa.core.views.admin.viewextensions'),
    (r'^core/extensions/save/$', 'modoboa.core.views.admin.saveextensions'),
    (r'^core/info/$', 'modoboa.core.views.admin.information'),
    (r'^core/logs/$', 'modoboa.core.views.admin.logs'),

    (r'^user/$', 'modoboa.core.views.user.index'),
    (r'^user/preferences/$', 'modoboa.core.views.user.preferences'),
    (r'^user/profile/$', 'modoboa.core.views.user.profile'),
)
