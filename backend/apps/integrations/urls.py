from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DagChainNodeViewSet, DagChainProfileViewSet, IntegrationConnectionViewSet, webhook,
)

router = DefaultRouter()
router.register("integrations/connections", IntegrationConnectionViewSet, basename="integration")
router.register("dagchain-profiles", DagChainProfileViewSet, basename="dagchain-profile")
router.register("dagchain-nodes", DagChainNodeViewSet, basename="dagchain-node")

urlpatterns = router.urls + [
    path("integrations/<str:platform>/<int:conn_id>/webhook/", webhook),
    path("integrations/<str:platform>/webhook/", webhook),  # legacy (first conn)
]
