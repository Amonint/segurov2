from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Broker

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Broker model
    """
    list_display = ('name', 'ruc', 'contact_person', 'commission_percentage', 'phone', 'email', 'is_active')
    list_filter = ('is_active', 'commission_percentage', 'created_at')
    search_fields = ('name', 'ruc', 'contact_person', 'email')
    ordering = ('name',)

    fieldsets = (
        (_('Información básica'), {
            'fields': ('name', 'ruc', 'commission_percentage', 'is_active')
        }),
        (_('Información de contacto'), {
            'fields': ('address', 'phone', 'email', 'contact_person')
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
