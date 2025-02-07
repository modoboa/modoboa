"""Parameters API urls."""

from rest_framework import routers

from . import viewsets


router = routers.SimpleRouter()
router.register(
    r"parameters/global", viewsets.GlobalParametersViewSet, basename="parameter-global"
)
router.register(
    r"parameters/user", viewsets.UserParametersViewSet, basename="parameter-user"
)
urlpatterns = router.urls
