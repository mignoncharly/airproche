import hashlib

from django.core.cache import cache
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .marketplace_serializers import (
    DriverDirectorySerializer,
    DriverInquiryCreateSerializer,
    DriverInquirySerializer,
    DriverProfileSerializer,
    InquiryNoteCreateSerializer,
    InquiryTransitionSerializer,
)
from .marketplace_services import create_inquiry, transition_inquiry
from .models import DriverInquiry, InquiryNote, MarketplaceDriverProfile
from apps.locations.models import Airport, ServiceArea
from apps.locations.serializers import AirportListSerializer, ServiceAreaListSerializer


def published_drivers():
    return (
        MarketplaceDriverProfile.objects.filter(
            is_published=True,
            verification_status=MarketplaceDriverProfile.VerificationStatus.VERIFIED,
            airports__is_active=True,
        )
        .select_related("marketplace_vehicle")
        .prefetch_related("airports", "service_areas")
        .distinct()
    )


class MarketplacePagination(PageNumberPagination):
    page_size = 12
    max_page_size = 48
    page_size_query_param = "page_size"


class DriverDirectoryView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request):
        queryset = published_drivers()
        params = request.query_params
        if params.get("airport"):
            queryset = queryset.filter(
                Q(airports__slug=params["airport"]) | Q(airports__public_id=params["airport"])
            )
        if params.get("service_area"):
            queryset = queryset.filter(
                Q(service_areas__slug=params["service_area"])
                | Q(service_areas__public_id=params["service_area"])
            )
        if params.get("q"):
            query = params["q"].strip()[:100]
            queryset = queryset.filter(
                Q(display_name__icontains=query)
                | Q(business_name__icontains=query)
                | Q(service_areas__name__icontains=query)
                | Q(airports__name__icontains=query)
            )
        if params.get("direction"):
            queryset = queryset.filter(directions__contains=[params["direction"]])
        if params.get("language"):
            queryset = queryset.filter(languages__contains=[params["language"]])
        if params.get("passengers", "").isdigit():
            queryset = queryset.filter(max_passengers__gte=int(params["passengers"]))
        vehicle_filters = {}
        if params.get("vehicle_category"):
            vehicle_filters["marketplace_vehicle__category"] = params["vehicle_category"]
        if params.get("accessible") == "true":
            vehicle_filters["marketplace_vehicle__wheelchair_accessible"] = True
        if params.get("child_seat") == "true":
            vehicle_filters["marketplace_vehicle__child_seat"] = True
        if params.get("luggage", "").isdigit():
            vehicle_filters["marketplace_vehicle__luggage_capacity__gte"] = int(params["luggage"])
        queryset = queryset.filter(**vehicle_filters).distinct()
        ordering = {
            "response_time": ("typical_response_minutes", "display_name"),
            "experience": ("-years_experience", "display_name"),
            "newest": ("-published_at", "display_name"),
            "verified": ("-verified_at", "display_name"),
        }.get(params.get("sort"), ("display_name",))
        queryset = queryset.order_by(*ordering)
        paginator = MarketplacePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            DriverDirectorySerializer(page, many=True, context={"request": request}).data
        )


class DriverDirectoryDetailView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request, identifier):
        driver = (
            published_drivers()
            .filter(
                Q(slug=identifier) | Q(public_id=identifier)
                if self._uuid(identifier)
                else Q(slug=identifier)
            )
            .first()
        )
        if not driver:
            return Response({"detail": "Chauffeur introuvable."}, status=404)
        return Response(DriverDirectorySerializer(driver, context={"request": request}).data)

    @staticmethod
    def _uuid(value):
        try:
            import uuid

            uuid.UUID(str(value))
            return True
        except ValueError:
            return False


@method_decorator(csrf_protect, name="dispatch")
class DriverInquiryCreateView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)
    throttle_scope = "driver_inquiry"

    def post(self, request):
        serializer = DriverInquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.pop("website", ""):
            return Response(
                {"message": "Votre demande a été reçue."}, status=status.HTTP_202_ACCEPTED
            )
        driver = data.pop("driver")
        airport = data.pop("airport")
        remote = request.META.get("REMOTE_ADDR", "")
        recipient_key = hashlib.sha256(f"{driver.public_id}:{remote}".encode()).hexdigest()
        cache_key = f"marketplace-inquiry-recipient:{recipient_key}"
        if cache.add(cache_key, 1, timeout=3600) is False:
            try:
                count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=3600)
                count = 1
            if count > 5:
                raise Throttled(
                    detail="Trop de demandes ont été envoyées à ce chauffeur. Réessayez plus tard."
                )
        inquiry, duplicate = create_inquiry(
            driver=driver,
            airport=airport,
            data=data,
            idempotency_key=request.headers.get("Idempotency-Key", ""),
            remote_addr=remote,
        )
        inquiry.refresh_from_db()
        return Response(
            {
                "public_id": inquiry.public_id,
                "reference": inquiry.reference,
                "idempotent_replay": duplicate,
                "notification_state": "pending"
                if inquiry.status == DriverInquiry.Status.NEW
                else "sent",
                "message": (
                    f"Votre demande a été transmise à {driver.display_name}. Le trajet n’est "
                    "pas encore confirmé. Le chauffeur vous contactera directement pour "
                    "confirmer sa disponibilité, le tarif et les modalités."
                ),
            },
            status=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class MyDriverProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profile = (
            MarketplaceDriverProfile.objects.filter(user=request.user)
            .prefetch_related("airports", "service_areas")
            .first()
        )
        return Response(DriverProfileSerializer(profile).data if profile else None)

    def post(self, request):
        if MarketplaceDriverProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "Un profil chauffeur existe déjà."}, status=409)
        data = request.data.copy()
        data.setdefault("first_name", request.user.first_name)
        data.setdefault("last_name", request.user.last_name)
        data.setdefault(
            "display_name", f"{request.user.first_name} {request.user.last_name}".strip()
        )
        data.setdefault("professional_email", request.user.email)
        data.setdefault("phone", request.user.phone)
        serializer = DriverProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = MarketplaceDriverProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Créez d’abord votre profil chauffeur."}, status=404)
        serializer = DriverProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        next_status = profile.verification_status
        if next_status in {
            MarketplaceDriverProfile.VerificationStatus.VERIFIED,
            MarketplaceDriverProfile.VerificationStatus.UNDER_REVIEW,
        }:
            next_status = MarketplaceDriverProfile.VerificationStatus.SUBMITTED
        serializer.save(verification_status=next_status, is_published=False, published_at=None)
        return Response(serializer.data)


class DriverOnboardingOptionsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
            "airports": AirportListSerializer(Airport.objects.filter(is_active=True), many=True).data,
            "service_areas": ServiceAreaListSerializer(ServiceArea.objects.filter(is_active=True), many=True).data,
        })


class MyDriverInquiryListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = (
            DriverInquiry.objects.filter(driver__user=request.user)
            .select_related("airport", "consent")
            .prefetch_related("status_history", "notes")
        )
        params = request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("airport"):
            queryset = queryset.filter(
                Q(airport__slug=params["airport"]) | Q(airport__public_id=params["airport"])
            )
        if params.get("q"):
            q = params["q"][:100]
            queryset = queryset.filter(
                Q(reference__icontains=q)
                | Q(customer_name__icontains=q)
                | Q(destination__icontains=q)
            )
        if params.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=params["date_to"])
        queryset = queryset.order_by(
            "created_at" if params.get("sort") == "oldest" else "-created_at"
        )
        paginator = MarketplacePagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, request)
        response = paginator.get_paginated_response(DriverInquirySerializer(page, many=True).data)
        response.data["unread_count"] = DriverInquiry.objects.filter(
            driver__user=request.user,
            status__in=(DriverInquiry.Status.NEW, DriverInquiry.Status.NOTIFIED),
        ).count()
        return response


class MyDriverInquiryDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, request, public_id):
        inquiry = (
            DriverInquiry.objects.filter(public_id=public_id, driver__user=request.user)
            .select_related("airport", "consent")
            .prefetch_related("status_history", "notes")
            .first()
        )
        if not inquiry:
            from rest_framework.exceptions import NotFound

            raise NotFound("Demande introuvable.")
        return inquiry

    def get(self, request, public_id):
        inquiry = self.get_object(request, public_id)
        if inquiry.status in {DriverInquiry.Status.NEW, DriverInquiry.Status.NOTIFIED}:
            inquiry = transition_inquiry(
                inquiry=inquiry, actor=request.user, to_status=DriverInquiry.Status.VIEWED
            )
        return Response(DriverInquirySerializer(inquiry).data)


@method_decorator(csrf_protect, name="dispatch")
class MyDriverInquiryTransitionView(MyDriverInquiryDetailView):
    def post(self, request, public_id):
        inquiry = self.get_object(request, public_id)
        serializer = InquiryTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            inquiry = transition_inquiry(
                inquiry=inquiry,
                actor=request.user,
                to_status=serializer.validated_data["status"],
                note=serializer.validated_data.get("note", ""),
                customer_visible_note=serializer.validated_data.get("customer_visible_note", ""),
            )
        except ValueError as exc:
            raise ValidationError({"status": str(exc)}) from exc
        return Response(DriverInquirySerializer(inquiry).data)


@method_decorator(csrf_protect, name="dispatch")
class MyDriverInquiryNoteView(MyDriverInquiryDetailView):
    def post(self, request, public_id):
        inquiry = self.get_object(request, public_id)
        serializer = InquiryNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        InquiryNote.objects.create(
            inquiry=inquiry, author=request.user, **serializer.validated_data
        )
        return Response(DriverInquirySerializer(inquiry).data, status=201)
