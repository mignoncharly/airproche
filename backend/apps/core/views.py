from django.db import connection
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("ok", "unavailable"))


@method_decorator(never_cache, name="dispatch")
class LiveHealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=HealthResponseSerializer)
    def get(self, request):
        return JsonResponse({"status": "ok"})


@method_decorator(never_cache, name="dispatch")
class ReadyHealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=HealthResponseSerializer)
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return JsonResponse({"status": "unavailable"}, status=503)
        return JsonResponse({"status": "ok"})
