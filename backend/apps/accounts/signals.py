from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

ROLE_NAMES = ("Operations", "Dispatcher", "Finance", "Content manager", "Administrator")


@receiver(post_migrate)
def ensure_staff_roles(sender, **kwargs):
    if not apps.ready:
        return
    groups = {name: Group.objects.get_or_create(name=name)[0] for name in ROLE_NAMES}

    content_permissions = Permission.objects.filter(
        content_type__app_label="content",
        codename__in=(
            "add_businesssettings",
            "change_businesssettings",
            "view_businesssettings",
            "add_servicecontent",
            "change_servicecontent",
            "delete_servicecontent",
            "view_servicecontent",
            "add_faq",
            "change_faq",
            "delete_faq",
            "view_faq",
            "add_testimonial",
            "change_testimonial",
            "delete_testimonial",
            "view_testimonial",
            "add_legaldocument",
            "change_legaldocument",
            "delete_legaldocument",
            "view_legaldocument",
        ),
    )
    groups["Content manager"].permissions.set(content_permissions)

    view_user = Permission.objects.filter(content_type__app_label="accounts", codename="view_user")
    groups["Operations"].permissions.add(*view_user)

    coverage_permissions = Permission.objects.filter(
        content_type__app_label__in=("locations", "pricing"),
        content_type__model__in=("airport", "servicearea", "tariff", "tariffoption"),
    )
    quote_view = Permission.objects.filter(content_type__app_label="pricing", codename="view_quote")
    groups["Operations"].permissions.add(*coverage_permissions, *quote_view)
    operation_permissions = Permission.objects.filter(
        content_type__app_label="operations",
        content_type__model__in=("driver", "vehicle", "driverassignment", "auditevent"),
    )
    booking_permissions = Permission.objects.filter(
        content_type__app_label="bookings",
        codename__in=("view_booking", "change_booking", "add_bookingnote"),
    )
    payment_permissions = Permission.objects.filter(
        content_type__app_label="payments",
        codename__in=("view_payment", "view_refund", "change_payment"),
    )
    groups["Operations"].permissions.add(*operation_permissions, *booking_permissions, *payment_permissions)
    groups["Dispatcher"].permissions.add(*Permission.objects.filter(
        content_type__app_label="operations",
        codename__in=("view_driver", "view_vehicle", "view_driverassignment", "change_driverassignment", "view_auditevent"),
    ), *Permission.objects.filter(content_type__app_label="bookings", codename__in=("view_booking", "change_booking", "add_bookingnote")))
    groups["Finance"].permissions.add(*Permission.objects.filter(content_type__app_label="payments", codename__in=("view_payment", "view_refund", "change_payment")), *Permission.objects.filter(content_type__app_label="bookings", codename="view_booking"))
    groups["Administrator"].permissions.add(*operation_permissions, *booking_permissions, *payment_permissions)
