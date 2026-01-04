from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Asset

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Admin configuration for Asset model
    """
    list_display = ('asset_code', 'name', 'asset_type', 'custodian', 'location', 'acquisition_cost', 'current_value', 'condition_status', 'is_insured')
    list_filter = ('asset_type', 'condition_status', 'is_insured', 'acquisition_date', 'custodian', 'responsible_user')
    search_fields = ('asset_code', 'name', 'brand', 'model', 'serial_number', 'custodian__username', 'responsible_user__username')
    ordering = ('asset_code',)
    raw_id_fields = ('custodian', 'responsible_user', 'insurance_policy')

    fieldsets = (
        (_('Información básica'), {
            'fields': ('asset_code', 'name', 'description', 'asset_type', 'location')
        }),
        (_('Especificaciones'), {
            'fields': ('brand', 'model', 'serial_number'),
            'classes': ('collapse',)
        }),
        (_('Información financiera'), {
            'fields': ('acquisition_date', 'acquisition_cost', 'current_value')
        }),
        (_('Estado y condición'), {
            'fields': ('condition_status',)
        }),
        (_('Responsables'), {
            'fields': ('custodian', 'responsible_user')
        }),
        (_('Seguro'), {
            'fields': ('is_insured', 'insurance_policy'),
            'classes': ('collapse',)
        }),
        (_('Fechas del sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('asset_code', 'created_at', 'updated_at')

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related(
            'custodian', 'responsible_user', 'insurance_policy'
        )

    actions = ['update_current_values']

    def update_current_values(self, request, queryset):
        """
        Action to update current values for selected assets
        """
        updated = 0
        for asset in queryset:
            asset.update_current_value()
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d activo actualizado.',
                '%d activos actualizados.',
                updated,
            ) % updated,
        )
    update_current_values.short_description = _('Actualizar valores actuales de los activos seleccionados')
