from __future__ import annotations

import hashlib
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseNotModified, JsonResponse
from django.utils import timezone
from django.utils.cache import patch_cache_control
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import FAQ, BusinessSettings, LegalDocument, ServiceContent, Testimonial
from .serializers import (
    BusinessSettingsPublicSerializer,
    FAQPublicSerializer,
    LegalDocumentPublicSerializer,
    PublicContentSerializer,
    ServiceContentPublicSerializer,
    TestimonialPublicSerializer,
)


def published_legal_documents() -> list[LegalDocument]:
    documents: list[LegalDocument] = []
    for kind, _label in LegalDocument.Kind.choices:
        document = (
            LegalDocument.objects.filter(
                kind=kind, is_published=True, effective_at__lte=timezone.now()
            )
            .order_by("-effective_at")
            .first()
        )
        if document:
            documents.append(document)
    return documents


class PublicContentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=PublicContentSerializer)
    def get(self, request):
        settings_instance = BusinessSettings.objects.first() or BusinessSettings()
        payload = {
            "settings": BusinessSettingsPublicSerializer(settings_instance).data,
            "services": ServiceContentPublicSerializer(
                ServiceContent.objects.filter(is_active=True), many=True
            ).data,
            "faqs": FAQPublicSerializer(FAQ.objects.filter(is_active=True), many=True).data,
            "testimonials": TestimonialPublicSerializer(
                Testimonial.objects.filter(is_active=True, verified_at__isnull=False), many=True
            ).data,
            "legal_documents": LegalDocumentPublicSerializer(
                published_legal_documents(), many=True
            ).data,
        }
        encoded = json.dumps(
            payload, cls=DjangoJSONEncoder, ensure_ascii=False, sort_keys=True
        ).encode()
        etag = f'"{hashlib.sha256(encoded).hexdigest()}"'
        if request.headers.get("If-None-Match") == etag:
            response = HttpResponseNotModified()
        else:
            response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
        response["ETag"] = etag
        patch_cache_control(response, public=True, max_age=60)
        return response
