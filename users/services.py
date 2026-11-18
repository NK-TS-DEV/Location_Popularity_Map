# users/services.py
import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from users.token import email_verification_token

logger = logging.getLogger(__name__)
User = get_user_model()


def _decode_user(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


class AuthService:
    @staticmethod
    def _send_action_email(*, user, subject, title, intro, button_text, link):
        html = render_to_string(
            "users/emails/action_email.html",
            {
                "username": user.username,
                "title": title,
                "intro": intro,
                "button_text": button_text,
                "link": link,
            },
        )
        send_mail(
            subject=subject,
            message=f"{intro}\n\n{link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html,
            fail_silently=False,
        )

    @staticmethod
    def send_verification_email(request, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        link = request.build_absolute_uri(
            reverse("verify_email", kwargs={"uidb64": uid, "token": token})
        )
        AuthService._send_action_email(
            user=user,
            subject="Confirm your email - Location Popularity Map",
            title="Confirm your email",
            intro="Thank you for registering! Please confirm your email address to activate your account.",
            button_text="Confirm email",
            link=link,
        )


    @staticmethod
    def register_user(validated_data, request):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)

        try:
            AuthService.send_verification_email(request, user)
        except Exception:
            logger.exception("Verification email failed for user %s", user.pk)

        return user

    @staticmethod
    def verify_email(uidb64, token):
        user = _decode_user(uidb64)
        if user is None:
            raise ValidationError("Invalid verification link.")

        if user.is_email_verified:
            return user

        if not email_verification_token.check_token(user, token):
            raise ValidationError("Verification link is invalid or expired.")

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return user

    @staticmethod
    def resend_verification_email(request, email):
        user = User.objects.filter(
            email__iexact=email, is_active=True, is_email_verified=False
        ).first()
        if user:
            try:
                AuthService.send_verification_email(request, user)
            except Exception:
                logger.exception("Verification email failed for user %s", user.pk)
        return True


    @staticmethod
    def login_user(request, email, password):
        user_obj = User.objects.filter(email__iexact=email).first()
        if user_obj is None:
            raise ValidationError("Invalid email or password.")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is None:
            raise ValidationError("Invalid email or password.")

        if not user.is_email_verified:
            raise ValidationError("Email is not confirmed. Please check your inbox.")

        login(request, user)
        return user

    @staticmethod
    def logout_user(request):
        logout(request)


    @staticmethod
    def request_password_reset(request, email):
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return True

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = request.build_absolute_uri(
            reverse("password_reset_page", kwargs={"uidb64": uid, "token": token})
        )

        try:
            AuthService._send_action_email(
                user=user,
                subject="Password reset - Location Popularity Map",
                title="Reset your password",
                intro="We received a request to reset your password. Click the button below to choose a new one.",
                button_text="Reset password",
                link=link,
            )
        except Exception:
            logger.exception("Password reset email failed for user %s", user.pk)
        return True

    @staticmethod
    def get_user_by_reset_token(uidb64, token):
        user = _decode_user(uidb64)
        if user is None:
            raise ValidationError("Invalid link or user.")
        if not default_token_generator.check_token(user, token):
            raise ValidationError("Token is invalid or expired.")
        return user

    @staticmethod
    def confirm_password_reset(uidb64, token, new_password):
        user = AuthService.get_user_by_reset_token(uidb64, token)
        validate_password(new_password, user)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return True