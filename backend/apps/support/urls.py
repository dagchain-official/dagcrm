from rest_framework.routers import DefaultRouter

from .views import TicketCommentViewSet, TicketViewSet

router = DefaultRouter()
router.register("tickets", TicketViewSet)
router.register("ticket-comments", TicketCommentViewSet)

urlpatterns = router.urls
