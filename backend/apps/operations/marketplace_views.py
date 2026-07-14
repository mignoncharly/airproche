from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .marketplace_serializers import DriverDirectorySerializer, DriverInquiryCreateSerializer, DriverInquirySerializer, DriverProfileSerializer
from .models import DriverInquiry, MarketplaceDriverProfile


def published_drivers():
    return MarketplaceDriverProfile.objects.filter(is_published=True, verification_status=MarketplaceDriverProfile.VerificationStatus.VERIFIED).prefetch_related("airports", "service_areas")


class DriverDirectoryView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request):
        queryset = published_drivers()
        airport = request.query_params.get("airport")
        area = request.query_params.get("service_area")
        if airport:
            queryset = queryset.filter(Q(airports__slug=airport) | Q(airports__public_id=airport))
        if area:
            queryset = queryset.filter(Q(service_areas__slug=area) | Q(service_areas__public_id=area))
        return Response(DriverDirectorySerializer(queryset.distinct(), many=True).data)


class DriverDirectoryDetailView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request, public_id):
        driver = published_drivers().filter(public_id=public_id).first()
        if not driver:
            return Response({"detail": "Chauffeur introuvable."}, status=404)
        return Response(DriverDirectorySerializer(driver).data)


@method_decorator(csrf_protect, name="dispatch")
class DriverInquiryCreateView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)
    throttle_scope = "driver_inquiry"

    def post(self, request):
        serializer = DriverInquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = serializer.save()
        return Response({"public_id": inquiry.public_id, "message": "Demande transmise. Elle ne constitue ni une reservation ni un prix confirme."}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class MyDriverProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profile = MarketplaceDriverProfile.objects.filter(user=request.user).prefetch_related("airports", "service_areas").first()
        return Response(DriverProfileSerializer(profile).data if profile else None)

    def post(self, request):
        if MarketplaceDriverProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "Un profil chauffeur existe deja."}, status=409)
        data = request.data.copy()
        data.setdefault("display_name", f"{request.user.first_name} {request.user.last_name}".strip())
        data.setdefault("phone", request.user.phone)
        serializer = DriverProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = MarketplaceDriverProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Creez d'abord votre profil chauffeur."}, status=404)
        serializer = DriverProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(verification_status=MarketplaceDriverProfile.VerificationStatus.PENDING, is_published=False)
        return Response(serializer.data)


class MyDriverInquiryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        inquiries = DriverInquiry.objects.filter(driver__user=request.user).select_related("airport")[:200]
        return Response(DriverInquirySerializer(inquiries, many=True).data)
