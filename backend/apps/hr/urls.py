from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityHeartbeatView, ActivityTodayView, AttendanceTodayView, AttendanceViewSet,
    CheckInView, CheckOutView, CostCategoryViewSet, DepartmentViewSet, EmployeeActivityViewSet,
    EmployeeCostViewSet, EmployeeViewSet, HierarchyLevelViewSet, IncentiveRuleViewSet,
    ActivityIncentiveViewSet, IncentiveSlabViewSet, IncentiveViewSet, LeaveTypeViewSet,
    LeaveViewSet, MyLeavesView, PayrollViewSet, PerformanceWeightViewSet, TargetMultiplierViewSet,
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
router.register("payrolls", PayrollViewSet)
router.register("incentive-rules", IncentiveRuleViewSet)
router.register("incentives", IncentiveViewSet)
router.register("target-multipliers", TargetMultiplierViewSet)
router.register("performance-weights", PerformanceWeightViewSet)
router.register("incentive-slabs", IncentiveSlabViewSet)
router.register("activity-incentives", ActivityIncentiveViewSet)

# Explicit self-service paths MUST come before router (so "check-in" isn't
# parsed as an attendance pk by the detail route).
urlpatterns = [
    path("attendance/check-in/", CheckInView.as_view()),
    path("attendance/check-out/", CheckOutView.as_view()),
    path("attendance/today/", AttendanceTodayView.as_view()),
    path("activity/today/", ActivityTodayView.as_view()),
    path("activity/heartbeat/", ActivityHeartbeatView.as_view()),
    path("my-leaves/", MyLeavesView.as_view()),
] + router.urls
