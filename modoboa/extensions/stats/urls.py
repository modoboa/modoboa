from django.conf.urls import patterns, url


urlpatterns = patterns(
    'modoboa.extensions.stats.views',

    url(r'^$', 'index', name='fullindex'),
    url(r'^graphs/$', "graphs", name="graph_list"),
    url(r'^domains/$', "get_domain_list", name="domain_list"),
)
