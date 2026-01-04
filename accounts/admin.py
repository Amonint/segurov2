from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    """
    Admin configuration for UserProfile model
    """
    list_display = ('username', 'email', 'full_name', 'role', 'department', 'is_active', 'created_at')
    list_filter = ('role', 'department', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'email', 'full_name', 'department')
    ordering = ('-created_at',)

    fieldsets = UserAdmin.fieldsets + (
        (_('Información adicional'), {
            'fields': ('full_name', 'role', 'department', 'phone')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Información adicional'), {
            'fields': ('full_name', 'role', 'department', 'phone', 'email')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        """
        Return queryset for admin list view
        """
        return super().get_queryset(request).select_related()
