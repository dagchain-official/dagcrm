from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IntegrationConnectionViewSet, webhook

router = DefaultRouter()
router.register("integrations/connections", IntegrationConnectionViewSet, basename="integration")

urlpatterns = router.urls + [
    path("integrations/<str:platform>/webhook/", webhook),
]
