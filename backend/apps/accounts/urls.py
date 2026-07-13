from django.urls import path

from .views import (
    CsrfView,
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="csrf"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("verify-email/resend/", ResendVerificationView.as_view(), name="resend-verification"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"
    ),
]
