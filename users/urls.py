# users/urls.py
from django.urls import path
from .views import (
    RegisterAPIView,
    ResendVerificationView,
    LoginAPIView,
    LogoutAPIView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    verify_email_page,
    password_reset_page,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("reset-confirm/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    path("verify-email/<str:uidb64>/<str:token>/", verify_email_page, name="verify_email"),
    path("reset-password/<str:uidb64>/<str:token>/", password_reset_page, name="password_reset_page"),
]