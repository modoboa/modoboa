from django.conf.urls import patterns, include, url
from django.conf import settings
from modoboa.core.extensions import exts_pool
from modoboa.lib import parameters
from modoboa.core import load_settings

load_settings()

urlpatterns = patterns('',
    (r'^$', 'modoboa.lib.webutils.topredirection'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('modoboa', ), }),

    (r'^accounts/login/$', 'modoboa.core.views.auth.dologin'),
    (r'^accounts/logout/$', 'modoboa.core.views.auth.dologout'),

    (r'^admin/$', 'modoboa.core.views.admin.viewsettings'),
    (r'^admin/parameters/$', 'modoboa.core.views.admin.viewparameters'),
    (r'^admin/parameters/save/$', 'modoboa.core.views.admin.saveparameters'),
    (r'^admin/extensions/$', 'modoboa.core.views.admin.viewextensions'),
    (r'^admin/extensions/save/$', 'modoboa.core.views.admin.saveextensions'),
    (r'^admin/info/$', 'modoboa.core.views.admin.information'),
    (r'^admin/logs/$', 'modoboa.core.views.admin.logs'),

    (r'^user/$', 'modoboa.core.views.user.index'),
    (r'^user/preferences/$', 'modoboa.core.views.user.preferences'),
    (r'^user/profile/$', 'modoboa.core.views.user.profile'),

    *exts_pool.load_all()
)

parameters.apply_to_django_settings()

if 'modoboa.demo' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^demo/', include('modoboa.demo.urls'))
    )

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
