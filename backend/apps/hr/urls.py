from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityHeartbeatView, ActivityTodayView, AttendanceTodayView, AttendanceViewSet,
    CandidateViewSet, CheckInView, CheckOutView, CostCategoryViewSet, DepartmentViewSet,
    EmployeeActivityViewSet, EmployeeCostViewSet, EmployeeViewSet, HierarchyLevelViewSet,
    IncentiveRuleViewSet, ActivityIncentiveViewSet, FormulaRuleViewSet, IncentiveSlabViewSet,
    IncentiveViewSet, JobPostingViewSet, LeaveTypeViewSet, LeaveViewSet, MyLeavesView,
    PayrollViewSet, PerformanceWeightViewSet, PublicJobView, TargetMultiplierViewSet,
    TrainingModuleViewSet, TrainingAssignmentViewSet, AssessmentViewSet, HRRequestViewSet,
    EmployeeDocumentViewSet, EmployeeEventViewSet, PerformanceJournalViewSet,
    AppraisalViewSet, PIPViewSet, EmployeeExitViewSet, HRTicketViewSet,
    PolicyViewSet, RecognitionViewSet, ProfileChangeRequestViewSet,
    VisaCaseViewSet, PolicySignatureViewSet,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet)
router.register("hierarchy-levels", HierarchyLevelViewSet)
router.register("cost-categories", CostCategoryViewSet)
router.register("employee-costs", EmployeeCostViewSet)
router.register("employees", EmployeeViewSet)
router.register("attendance", AttendanceViewSet)
router.register("employee-activities", EmployeeActivityViewSet)
router.register("leave-types", LeaveTypeViewSet)
router.register("leaves", LeaveViewSet)
router.register("hr-requests", HRRequestViewSet)
router.register("payrolls", PayrollViewSet)
router.register("incentive-rules", IncentiveRuleViewSet)
router.register("incentives", IncentiveViewSet)
router.register("target-multipliers", TargetMultiplierViewSet)
router.register("performance-weights", PerformanceWeightViewSet)
router.register("incentive-slabs", IncentiveSlabViewSet)
router.register("activity-incentives", ActivityIncentiveViewSet)
router.register("formula-rules", FormulaRuleViewSet)
router.register("job-postings", JobPostingViewSet)
router.register("candidates", CandidateViewSet)
router.register("training-modules", TrainingModuleViewSet)
router.register("training-assignments", TrainingAssignmentViewSet)
router.register("assessments", AssessmentViewSet)
router.register("employee-documents", EmployeeDocumentViewSet)
router.register("employee-events", EmployeeEventViewSet)
router.register("performance-journal", PerformanceJournalViewSet)
router.register("appraisals", AppraisalViewSet)
router.register("pips", PIPViewSet)
router.register("employee-exits", EmployeeExitViewSet)
router.register("hr-tickets", HRTicketViewSet)
router.register("policies", PolicyViewSet)
router.register("recognitions", RecognitionViewSet)
router.register("profile-change-requests", ProfileChangeRequestViewSet)
router.register("visa-cases", VisaCaseViewSet)
router.register("policy-signatures", PolicySignatureViewSet)

# Explicit self-service paths MUST come before router (so "check-in" isn't
# parsed as an attendance pk by the detail route).
urlpatterns = [
    path("attendance/check-in/", CheckInView.as_view()),
    path("attendance/check-out/", CheckOutView.as_view()),
    path("attendance/today/", AttendanceTodayView.as_view()),
    path("activity/today/", ActivityTodayView.as_view()),
    path("activity/heartbeat/", ActivityHeartbeatView.as_view()),
    path("my-leaves/", MyLeavesView.as_view()),
    path("jobs/apply/<str:token>/", PublicJobView.as_view()),   # public job ad + apply
] + router.urls
