from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccessMetaView,
    ModulePermissionViewSet,
    RoleViewSet,
    TeamMemberViewSet,
    TeamViewSet,
    UserPermissionViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("roles", RoleViewSet)
router.register("users", UserViewSet)
router.register("user-permissions", UserPermissionViewSet)
router.register("module-permissions", ModulePermissionViewSet)
router.register("teams", TeamViewSet)
router.register("team-members", TeamMemberViewSet)

urlpatterns = router.urls + [
    path("access/meta/", AccessMetaView.as_view()),
]
