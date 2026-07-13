from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.cache import patch_cache_control
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Quote, Tariff, TariffOption
from .serializers import CoverageSerializer, QuoteRequestSerializer, QuoteSerializer
from .services import create_quote


def coverage_payload():
    now = timezone.now()
    tariffs = (
        Tariff.objects.filter(
            is_active=True,
            airport__is_active=True,
            service_area__is_active=True,
            valid_from__lte=now,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=now))
        .select_related("airport", "service_area")
        .order_by("-priority", "valid_from")
    )
    routes: list[dict] = []
    seen: set[tuple] = set()
    for tariff in tariffs:
        key = (tariff.airport.public_id, tariff.service_area.public_id, tariff.trip_type)
        if key in seen:
            continue
        seen.add(key)
        option_candidates = (
            TariffOption.objects.filter(is_active=True, valid_from__lte=now)
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=now))
            .filter(Q(tariff__isnull=True) | Q(tariff=tariff))
            .order_by("code", "-valid_from")
        )
        options: dict[str, TariffOption] = {}
        for option in option_candidates:
            existing = options.get(option.code)
            if not existing or (option.tariff_id and not existing.tariff_id):
                options[option.code] = option
        routes.append(
            {
                "airport_id": tariff.airport.public_id,
                "service_area_id": tariff.service_area.public_id,
                "trip_type": tariff.trip_type,
                "options": [
                    {
                        "code": option.code,
                        "label": option.label,
                        "pricing_method": option.pricing_method,
                        "maximum_quantity": option.maximum_quantity,
                    }
                    for option in options.values()
                ],
            }
        )
    return {"routes": routes}


class CoverageView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=CoverageSerializer)
    def get(self, request):
        response = Response(coverage_payload())
        patch_cache_control(response, public=True, max_age=60)
        return response


class QuoteCreateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "quote"

    @extend_schema(request=QuoteRequestSerializer, responses={201: QuoteSerializer})
    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quote = create_quote(serializer.validated_data)
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)


class QuoteDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "quote"

    @extend_schema(responses=QuoteSerializer)
    def get(self, request, public_id):
        quote = get_object_or_404(
            Quote.objects.select_related("airport", "service_area").prefetch_related("lines"),
            public_id=public_id,
        )
        response = Response(QuoteSerializer(quote).data)
        response["Cache-Control"] = "no-store"
        return response
