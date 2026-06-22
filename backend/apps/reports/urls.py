from django.urls import path

from . import views

urlpatterns = [
    path("reports/dashboard/", views.dashboard_summary),
    path("reports/my-dashboard/", views.my_dashboard),
    path("reports/team-dashboard/", views.team_dashboard),
    path("reports/hr-dashboard/", views.hr_dashboard),
    path("reports/finance-dashboard/", views.finance_dashboard),
    path("reports/support-dashboard/", views.support_dashboard),
    path("reports/sales-dashboard/", views.sales_dashboard),
    path("reports/leads-by-status/", views.leads_by_status),
    path("reports/leads-by-source/", views.leads_by_source),
    path("reports/opportunities-by-stage/", views.opportunities_by_stage),
    path("reports/revenue-by-business/", views.revenue_by_business),
    path("reports/revenue-trend/", views.revenue_trend),
]
