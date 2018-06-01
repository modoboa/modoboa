"""Parameters API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(
    r"parameters", viewsets.ParametersViewSet, base_name="parameter")
urlpatterns = router.urls
