"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from users.views import (
    LoginAPIView,
    LogoutAPIView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterAPIView,
    ResendVerificationView,
    password_reset_page,
    verify_email_page,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Location Popularity Map API",
        default_version="v1",
        description="API documentation for the Location Popularity Map project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(
            email="support@locationmap.app"),
        license=openapi.License(
            name="BSD License"),
    ),
    public=True,
    permission_classes=(
        permissions.AllowAny,
    ),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),

    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("accounts/profile/", RedirectView.as_view(url="/swagger/", permanent=False)),

    path("api/v1/users/register/", RegisterAPIView.as_view(), name="register"),
    path("api/v1/users/resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    path("api/v1/users/login/", LoginAPIView.as_view(), name="login"),
    path("api/v1/users/logout/", LogoutAPIView.as_view(), name="logout"),
    path("api/v1/users/password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("api/v1/users/reset-confirm/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),

    path("api/v1/users/verify-email/<str:uidb64>/<str:token>/", verify_email_page, name="verify_email"),
    path("api/v1/users/reset-password/<str:uidb64>/<str:token>/", password_reset_page, name="password_reset_page"),
    path("api/v1/", include("locations.urls")),


]
