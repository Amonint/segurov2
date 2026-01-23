from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import EmissionRights, InsuranceCompany


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    """
    Admin configuration for InsuranceCompany model
    """

    list_display = ("name", "ruc", "contact_person", "phone", "email", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "ruc", "contact_person", "email")
    ordering = ("name",)

    fieldsets = (
        (_("Información básica"), {"fields": ("name", "ruc", "is_active")}),
        (
            _("Información de contacto"),
            {"fields": ("address", "phone", "email", "contact_person")},
        ),
        (
            _("Fechas"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(EmissionRights)
class EmissionRightsAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmissionRights model
    """

    list_display = ("min_amount", "max_amount", "emission_right", "created_at")
    list_filter = ("created_at",)
    search_fields = ("min_amount", "max_amount")
    ordering = ("min_amount",)

    fieldsets = (
        (
            _("Configuración de rango"),
            {"fields": ("min_amount", "max_amount", "emission_right")},
        ),
        (_("Información"), {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    readonly_fields = ("created_at",)
