from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.extensions.sievefilters.views',

    url(r'^$', 'index', name="index"),
    url(r'^savefs/(?P<name>.+)/$', 'savefs', name="fs_save"),
    url(r'^newfs/$', 'new_filters_set', name="fs_add"),
    url(r'^removefs/(?P<name>.+)/$', 'remove_filters_set', name="fs_delete"),
    url(r'^activatefs/(?P<name>.+)/$', 'activate_filters_set',
        name="fs_activate"),
    url(r'^downloadfs/(?P<name>.+)/$', 'download_filters_set',
        name="fs_download"),
    url(r'^templates/(?P<ftype>\w+)/$', 'get_templates',
        name="templates_get"),
    url(r'^(?P<setname>.+)/newfilter/$', 'newfilter',
        name="filter_add"),
    url(r'^(?P<setname>.+)/editfilter/(?P<fname>.+)/$', 'editfilter',
        name="filter_change"),
    url(r'^(?P<setname>.+)/removefilter/(?P<fname>.+)/$', 'removefilter',
        name="filter_delete"),
    url(r'^(?P<setname>.+)/togglestate/(?P<fname>.+)/$',
        'toggle_filter_state', name="filter_toggle_state"),
    url(r'^(?P<setname>.+)/moveup/(?P<fname>.+)/$',
        'move_filter_up', name="filter_move_up"),
    url(r'^(?P<setname>.+)/movedown/(?P<fname>.+)/$',
        'move_filter_down', name="filter_move_down"),
    url(r'^(?P<name>.+)/$', 'getfs', name="fs_get"),
)
