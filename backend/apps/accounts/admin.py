from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import AccountToken, ConsentRecord, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone", "preferred_locale")}),
        (_("Verification"), {"fields": ("email_verified_at",)}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(AccountToken)
class AccountTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "created_at", "expires_at", "consumed_at")
    list_filter = ("purpose", "consumed_at")
    search_fields = ("user__email",)
    readonly_fields = (
        "user",
        "purpose",
        "token_digest",
        "created_at",
        "expires_at",
        "consumed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "consent_type", "document_version", "granted_at")
    list_filter = ("consent_type", "document_version")
    search_fields = ("user__email",)
    readonly_fields = (
        "public_id",
        "user",
        "consent_type",
        "document_version",
        "granted_at",
        "withdrawn_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
