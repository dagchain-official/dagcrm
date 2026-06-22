from rest_framework.routers import DefaultRouter

from .views import CommissionViewSet, ExpenseViewSet

router = DefaultRouter()
router.register("expenses", ExpenseViewSet)
router.register("commissions", CommissionViewSet)

urlpatterns = router.urls
