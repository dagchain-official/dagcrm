from django.urls import path
from rest_framework.routers import DefaultRouter

from . import fxartha_views as fx
from .views import IntegrationConnectionViewSet, webhook

router = DefaultRouter()
router.register("integrations/connections", IntegrationConnectionViewSet, basename="integration")

urlpatterns = router.urls + [
    path("integrations/<str:platform>/webhook/", webhook),
    # FX Artha external CRM proxy
    path("fxartha/status/", fx.fx_status),
    path("fxartha/dashboard/", fx.fx_dashboard),
    path("fxartha/leads/", fx.fx_leads),
    path("fxartha/customers/", fx.fx_customers),
    path("fxartha/import-leads/", fx.fx_import_leads),
]
