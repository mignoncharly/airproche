from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.cache import patch_cache_control
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Airport, ServiceArea
from .serializers import (
    AirportDetailSerializer,
    AirportListSerializer,
    ServiceAreaDetailSerializer,
    ServiceAreaListSerializer,
)


def public_response(data):
    response = Response(data)
    patch_cache_control(response, public=True, max_age=60)
    return response


def active_tariffs():
    from apps.pricing.models import Tariff

    now = timezone.now()
    return Tariff.objects.filter(
        is_active=True,
        airport__is_active=True,
        service_area__is_active=True,
        valid_from__lte=now,
    ).filter(Q(valid_until__isnull=True) | Q(valid_until__gt=now))


def published_service_areas():
    return ServiceArea.objects.filter(is_active=True, tariffs__in=active_tariffs()).distinct()


def published_airports():
    return Airport.objects.filter(is_active=True, tariffs__in=active_tariffs()).distinct()


class AirportListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=AirportListSerializer(many=True))
    def get(self, request):
        airports = published_airports()
        return public_response(AirportListSerializer(airports, many=True).data)


class AirportDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=AirportDetailSerializer)
    def get(self, request, slug: str):
        airport = get_object_or_404(published_airports(), slug=slug)
        return public_response(AirportDetailSerializer(airport).data)


class ServiceAreaListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=ServiceAreaListSerializer(many=True))
    def get(self, request):
        areas = published_service_areas()
        return public_response(ServiceAreaListSerializer(areas, many=True).data)


class ServiceAreaDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=ServiceAreaDetailSerializer)
    def get(self, request, slug: str):
        area = get_object_or_404(published_service_areas(), slug=slug)
        return public_response(ServiceAreaDetailSerializer(area).data)
