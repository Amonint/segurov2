from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model
    """

    list_display = (
        "user",
        "notification_type",
        "title",
        "priority",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "priority", "is_read", "created_at")
    search_fields = ("user__username", "user__full_name", "title", "message")
    ordering = ("-created_at",)
    raw_id_fields = ("user",)

    fieldsets = (
        (
            _("Información básica"),
            {"fields": ("user", "notification_type", "title", "message", "link")},
        ),
        (_("Estado"), {"fields": ("is_read", "priority")}),
        (
            _("Información del sistema"),
            {"fields": ("created_at",), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related("user")
