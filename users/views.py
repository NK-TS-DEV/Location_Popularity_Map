from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendVerificationSerializer,
    UserResponseSerializer,
    UserSerializerRegister,
)
from .services import AuthService



class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializerRegister
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.register_user(serializer.validated_data, request)
        return Response(
            {"detail": "Registration successful. Please check your email and confirm your account."},
            status=status.HTTP_201_CREATED,
        )


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=ResendVerificationSerializer)
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.resend_verification_email(request, serializer.validated_data["email"])
        return Response(
            {"detail": "If the account exists and is not confirmed, a new email has been sent."},
            status=status.HTTP_200_OK,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.login_user(
                request,
                serializer.validated_data["email"],
                serializer.validated_data["password"],
            )
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Successfully logged in!", "user": UserResponseSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        AuthService.logout_user(request)
        return Response({"detail": "Successfully logged out!"}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=PasswordResetRequestSerializer)
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.request_password_reset(request, serializer.validated_data["email"])
        return Response(
            {"detail": "If an account with this email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=PasswordResetConfirmSerializer)
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.confirm_password_reset(
                uidb64=uidb64,
                token=token,
                new_password=serializer.validated_data["new_password"],
            )
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Password successfully changed!"}, status=status.HTTP_200_OK)



def _page(request, *, title, message="", ok=True, show_form=False, errors=None, status_code=200):
    return render(
        request,
        "users/page.html",
        {"title": title, "message": message, "ok": ok, "show_form": show_form, "errors": errors or []},
        status=status_code,
    )


@require_GET
def verify_email_page(request, uidb64, token):
    try:
        AuthService.verify_email(uidb64, token)
    except ValidationError as e:
        return _page(request, title="Email confirmation", message=e.messages[0], ok=False, status_code=400)
    return _page(request, title="Email confirmed", message="Your email has been confirmed. You can now log in.")


@require_http_methods(["GET", "POST"])
def password_reset_page(request, uidb64, token):
    title = "Password reset"

    try:
        AuthService.get_user_by_reset_token(uidb64, token)
    except ValidationError as e:
        return _page(request, title=title, message=e.messages[0], ok=False, status_code=400)

    if request.method == "GET":
        return _page(request, title=title, show_form=True)

    password = request.POST.get("new_password", "")
    if password != request.POST.get("confirm_password", ""):
        return _page(request, title=title, show_form=True, errors=["Passwords do not match."])

    try:
        AuthService.confirm_password_reset(uidb64, token, password)
    except ValidationError as e:
        return _page(request, title=title, show_form=True, errors=e.messages)

    return _page(request, title="Password changed", message="Your password has been changed. You can now log in.")