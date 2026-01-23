from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for AuditLog model (read-only)
    """

    list_display = (
        "user",
        "action_type",
        "entity_type",
        "entity_id",
        "description",
        "ip_address",
        "created_at",
    )
    list_filter = ("action_type", "entity_type", "created_at", "user")
    search_fields = (
        "user__username",
        "user__full_name",
        "description",
        "ip_address",
        "user_agent",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("user", "content_type")

    fieldsets = (
        (
            _("Información básica"),
            {"fields": ("user", "action_type", "entity_type", "entity_id")},
        ),
        (
            _("Cambios realizados"),
            {"fields": ("old_values", "new_values"), "classes": ("collapse",)},
        ),
        (
            _("Información adicional"),
            {
                "fields": ("description", "ip_address", "user_agent"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Información del sistema"),
            {
                "fields": ("content_type", "object_id", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = (
        "user",
        "action_type",
        "entity_type",
        "entity_id",
        "old_values",
        "new_values",
        "description",
        "ip_address",
        "user_agent",
        "content_type",
        "object_id",
        "created_at",
    )

    def has_add_permission(self, request):
        """
        Audit logs cannot be added manually
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Audit logs should not be deleted (only by system admin if necessary)
        """
        return False

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related("user", "content_type")
