from django.conf.urls import include, path

urlpatterns = [
    path(r'', include('modoboa.urls')),
]
