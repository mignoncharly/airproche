from __future__ import annotations

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea

from .models import Quote, QuoteLine, Tariff, TariffOption

CENT = Decimal("0.01")


class QuoteUnavailable(APIException):
    status_code = 422
    default_detail = "Ce trajet ne peut pas être estimé en ligne."
    default_code = "quote_unavailable"


def unavailable(message: str, code: str) -> QuoteUnavailable:
    return QuoteUnavailable(detail=message, code=code)


def active_tariff(airport: Airport, area: ServiceArea, trip_type: str, at):
    return (
        Tariff.objects.filter(
            airport=airport,
            service_area=area,
            trip_type=trip_type,
            is_active=True,
            valid_from__lte=at,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=at))
        .order_by("-priority", "-valid_from")
        .first()
    )


def applicable_options(tariff: Tariff, at, requested_codes: list[str]):
    candidates = list(
        TariffOption.objects.filter(
            code__in=requested_codes,
            is_active=True,
            valid_from__lte=at,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=at))
        .filter(Q(tariff__isnull=True) | Q(tariff=tariff))
        .order_by("-valid_from")
    )
    selected: dict[str, TariffOption] = {}
    for code in requested_codes:
        matching = [option for option in candidates if option.code == code]
        specific = next((option for option in matching if option.tariff_id == tariff.id), None)
        if specific:
            selected[code] = specific
        elif matching:
            selected[code] = matching[0]
    return selected


@transaction.atomic
def create_quote(data: dict) -> Quote:
    now = timezone.now()
    settings = BusinessSettings.objects.first() or BusinessSettings()
    pickup_at = data["pickup_at"]
    if pickup_at < now + timedelta(hours=settings.minimum_lead_hours):
        raise unavailable(
            f"Le départ doit être prévu au moins {settings.minimum_lead_hours} heures à l’avance.",
            "lead_time",
        )
    if pickup_at > now + timedelta(days=settings.maximum_booking_days):
        raise unavailable(
            "La date dépasse l’horizon de réservation actuellement autorisé.",
            "booking_horizon",
        )

    try:
        airport = Airport.objects.get(public_id=data["airport_id"], is_active=True)
        area = ServiceArea.objects.get(public_id=data["service_area_id"], is_active=True)
    except (Airport.DoesNotExist, ServiceArea.DoesNotExist) as exc:
        raise unavailable("La zone demandée n’est pas disponible.", "coverage") from exc

    tariff = active_tariff(airport, area, data["trip_type"], pickup_at)
    if not tariff:
        raise unavailable("Aucun tarif actif ne couvre ce trajet à cette date.", "coverage")
    if data["passenger_count"] > tariff.passenger_capacity:
        raise unavailable("Le nombre de passagers nécessite une vérification manuelle.", "capacity")
    if data["luggage_count"] > tariff.luggage_capacity:
        raise unavailable("Le nombre de bagages nécessite une vérification manuelle.", "capacity")

    requested = {item["code"]: item["quantity"] for item in data.get("options", [])}
    selected = applicable_options(tariff, pickup_at, list(requested))
    if set(selected) != set(requested):
        raise unavailable("Une option sélectionnée n’est pas disponible.", "option_unavailable")

    line_values = [
        {
            "code": "base-fare",
            "label": f"Trajet {airport.iata_code} · {area.name}",
            "quantity": 1,
            "unit_amount": tariff.base_amount.quantize(CENT, rounding=ROUND_HALF_UP),
            "total_amount": tariff.base_amount.quantize(CENT, rounding=ROUND_HALF_UP),
            "display_order": 0,
        }
    ]
    total = line_values[0]["total_amount"]
    for index, (code, quantity) in enumerate(requested.items(), start=1):
        option = selected[code]
        if option.currency != tariff.currency or quantity > option.maximum_quantity:
            raise unavailable("Une option sélectionnée n’est pas disponible.", "option_unavailable")
        if option.pricing_method == TariffOption.PricingMethod.FIXED and quantity != 1:
            raise unavailable(
                "Cette option ne peut être sélectionnée qu’une fois.", "option_quantity"
            )
        line_total = (
            option.amount
            if option.pricing_method == TariffOption.PricingMethod.FIXED
            else option.amount * quantity
        )
        line_total = line_total.quantize(CENT, rounding=ROUND_HALF_UP)
        line_values.append(
            {
                "code": option.code,
                "label": option.label,
                "quantity": quantity,
                "unit_amount": option.amount.quantize(CENT, rounding=ROUND_HALF_UP),
                "total_amount": line_total,
                "display_order": index,
            }
        )
        total += line_total

    quote = Quote.objects.create(
        tariff=tariff,
        trip_type=data["trip_type"],
        airport=airport,
        service_area=area,
        airport_name=airport.name,
        airport_iata_code=airport.iata_code,
        service_area_name=area.name,
        pickup_at=pickup_at,
        passenger_count=data["passenger_count"],
        luggage_count=data["luggage_count"],
        total_amount=total.quantize(CENT, rounding=ROUND_HALF_UP),
        currency=tariff.currency,
        expires_at=now + timedelta(minutes=settings.quote_valid_minutes),
    )
    QuoteLine.objects.bulk_create([QuoteLine(quote=quote, **line) for line in line_values])
    return Quote.objects.prefetch_related("lines").get(pk=quote.pk)
