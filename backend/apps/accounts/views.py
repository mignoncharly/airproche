from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccountToken, ConsentRecord, User
from .serializers import (
    CsrfSerializer,
    EmailSerializer,
    LoginSerializer,
    MessageSerializer,
    PasswordResetConfirmSerializer,
    ProfileSerializer,
    RegisterSerializer,
    RegistrationResponseSerializer,
    SessionResponseSerializer,
    TokenSerializer,
    UserPublicSerializer,
)
from .services import (
    issue_account_token,
    registration_documents,
    reset_password_with_token,
    send_password_reset_email,
    send_verification_email,
    verify_email_token,
)


@method_decorator(never_cache, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=CsrfSerializer)
    def get(self, request):
        return Response({"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth_register"

    @extend_schema(request=RegisterSerializer, responses={201: RegistrationResponseSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        documents = registration_documents()
        if set(documents) != {"terms", "privacy"}:
            return Response(
                {
                    "error": {
                        "code": "registration_unavailable",
                        "message": (
                            "L’inscription sera ouverte après publication des documents légaux."
                        ),
                        "fields": None,
                        "request_id": getattr(request, "correlation_id", None),
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = serializer.validated_data.copy()
        data.pop("accept_terms")
        data.pop("accept_privacy")
        password = data.pop("password")
        try:
            with transaction.atomic():
                user = User.objects.create_user(password=password, **data)
                ConsentRecord.objects.bulk_create(
                    [
                        ConsentRecord(
                            user=user,
                            consent_type=ConsentRecord.ConsentType.TERMS,
                            document_version=documents["terms"].version,
                        ),
                        ConsentRecord(
                            user=user,
                            consent_type=ConsentRecord.ConsentType.PRIVACY,
                            document_version=documents["privacy"].version,
                        ),
                    ]
                )
                raw_token = issue_account_token(user, AccountToken.Purpose.VERIFY_EMAIL)
        except IntegrityError as exc:
            if User.objects.filter(email__iexact=data["email"]).exists():
                raise ValidationError(
                    {"email": "Un compte existe déjà pour cette adresse."}
                ) from exc
            raise

        sent = send_verification_email(user, raw_token)
        return Response(
            {
                "message": "Compte créé. Vérifiez votre adresse e-mail.",
                "verification_email_sent": sent,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    @extend_schema(request=LoginSerializer, responses=SessionResponseSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = User.objects.normalize_email(serializer.validated_data["email"]).lower()
        user = authenticate(
            request=request,
            username=email,
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise AuthenticationFailed("Adresse e-mail ou mot de passe incorrect.")
        login(request, user)
        return Response({"user": UserPublicSerializer(user).data})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SessionResponseSerializer)
    def get(self, request):
        return Response({"user": UserPublicSerializer(request.user).data})


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=MessageSerializer)
    def post(self, request):
        logout(request)
        return Response({"message": "Vous êtes déconnecté."})


@method_decorator(csrf_protect, name="dispatch")
class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth_token"

    @extend_schema(request=TokenSerializer, responses=MessageSerializer)
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_email_token(serializer.validated_data["token"])
        return Response({"message": "Votre adresse e-mail est vérifiée."})


@method_decorator(csrf_protect, name="dispatch")
class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_token"

    @extend_schema(request=None, responses=MessageSerializer)
    def post(self, request):
        if request.user.email_verified_at:
            return Response({"message": "Votre adresse e-mail est déjà vérifiée."})
        with transaction.atomic():
            raw_token = issue_account_token(request.user, AccountToken.Purpose.VERIFY_EMAIL)
        send_verification_email(request.user, raw_token)
        return Response({"message": "Si l’envoi est disponible, un nouveau lien a été envoyé."})


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth_password_reset"

    @extend_schema(request=EmailSerializer, responses=MessageSerializer)
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = User.objects.normalize_email(serializer.validated_data["email"]).lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            with transaction.atomic():
                raw_token = issue_account_token(user, AccountToken.Purpose.RESET_PASSWORD)
            send_password_reset_email(user, raw_token)
        return Response(
            {
                "message": (
                    "Si un compte correspond à cette adresse, un lien de "
                    "réinitialisation a été envoyé."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "auth_token"

    @extend_schema(request=PasswordResetConfirmSerializer, responses=MessageSerializer)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_password_with_token(
            serializer.validated_data["token"], serializer.validated_data["new_password"]
        )
        return Response({"message": "Votre mot de passe a été modifié."})


@method_decorator(csrf_protect, name="dispatch")
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ProfileSerializer, responses=SessionResponseSerializer)
    def patch(self, request):
        if not request.user.email_verified_at:
            raise PermissionDenied("Vérifiez votre adresse e-mail avant de modifier votre profil.")
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"user": UserPublicSerializer(request.user).data})
