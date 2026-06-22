from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    ChangePasswordView, ForgotPasswordView, LoginView, MeView, ProfileView,
    ResetPasswordView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # auth
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/auth/profile/", ProfileView.as_view(), name="profile"),
    path("api/auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("api/auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("api/auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    # api modules
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.crm.urls")),
    path("api/", include("apps.sales.urls")),
    path("api/", include("apps.support.urls")),
    path("api/", include("apps.hr.urls")),
    path("api/", include("apps.finance.urls")),
    path("api/", include("apps.reports.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.integrations.urls")),
    path("api/search/", include("apps.reports.search_urls")),
    # docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
