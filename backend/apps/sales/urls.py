from rest_framework.routers import DefaultRouter

from .views import RevenueViewSet

router = DefaultRouter()
router.register("revenues", RevenueViewSet)

urlpatterns = router.urls
