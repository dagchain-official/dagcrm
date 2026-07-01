from rest_framework.routers import DefaultRouter

from .views import (
    AttachmentViewSet, AumEntryViewSet, BusinessViewSet, CommunicationViewSet,
    ContributionEntryViewSet, ContributionWeightViewSet, CustomerProductViewSet,
    CustomerViewSet, LeadActivityViewSet, LeadInterestViewSet, LeadSourceViewSet,
    LeadViewSet, MetricDefinitionViewSet, MetricEntryViewSet, OpportunityViewSet,
    ProductViewSet, ProposalViewSet, TargetAssignmentViewSet, TargetViewSet,
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
router.register("metric-definitions", MetricDefinitionViewSet)
router.register("metric-entries", MetricEntryViewSet)
router.register("aum-entries", AumEntryViewSet)
router.register("contribution-entries", ContributionEntryViewSet)
router.register("contribution-weights", ContributionWeightViewSet)
router.register("attachments", AttachmentViewSet)
router.register("proposals", ProposalViewSet)

urlpatterns = router.urls
