from rest_framework.routers import DefaultRouter

from .views import (
    AttachmentViewSet, BusinessViewSet, CommunicationViewSet, CustomerProductViewSet,
    CustomerViewSet, LeadActivityViewSet, LeadInterestViewSet, LeadSourceViewSet,
    LeadViewSet, OpportunityViewSet, ProductViewSet, ProposalViewSet,
    TargetAssignmentViewSet, TargetViewSet,
)

router = DefaultRouter()
router.register("businesses", BusinessViewSet)
router.register("products", ProductViewSet)
router.register("lead-sources", LeadSourceViewSet)
router.register("leads", LeadViewSet)
router.register("lead-interests", LeadInterestViewSet)
router.register("lead-activities", LeadActivityViewSet)
router.register("opportunities", OpportunityViewSet)
router.register("customers", CustomerViewSet)
router.register("customer-products", CustomerProductViewSet)
router.register("communications", CommunicationViewSet)
router.register("targets", TargetViewSet)
router.register("target-assignments", TargetAssignmentViewSet)
router.register("attachments", AttachmentViewSet)
router.register("proposals", ProposalViewSet)

urlpatterns = router.urls
