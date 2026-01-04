from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Claim, ClaimDocument, ClaimTimeline

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    """
    Admin configuration for Claim model
    """
    list_display = ('claim_number', 'policy', 'incident_date', 'status', 'estimated_loss', 'approved_amount', 'reported_by', 'assigned_to')
    list_filter = ('status', 'incident_date', 'report_date', 'asset_type', 'reported_by', 'assigned_to', 'created_at')
    search_fields = ('claim_number', 'incident_description', 'asset_description', 'asset_code', 'policy__policy_number')
    ordering = ('-created_at',)
    raw_id_fields = ('policy', 'reported_by', 'assigned_to')

    fieldsets = (
        (_('Información básica'), {
            'fields': ('claim_number', 'policy', 'reported_by', 'assigned_to')
        }),
        (_('Información del incidente'), {
            'fields': ('incident_date', 'report_date', 'incident_location', 'incident_description')
        }),
        (_('Información del bien'), {
            'fields': ('asset_type', 'asset_description', 'asset_code')
        }),
        (_('Información financiera'), {
            'fields': ('estimated_loss', 'approved_amount', 'payment_date', 'rejection_reason')
        }),
        (_('Estado del workflow'), {
            'fields': ('status',)
        }),
        (_('Fechas del sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('claim_number', 'created_at', 'updated_at')

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related(
            'policy', 'reported_by', 'assigned_to'
        )

@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    """
    Admin configuration for ClaimDocument model
    """
    list_display = ('document_name', 'claim', 'document_type', 'file_size', 'is_required', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'is_required', 'uploaded_at', 'uploaded_by')
    search_fields = ('document_name', 'claim__claim_number', 'uploaded_by__username')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('claim', 'uploaded_by')

    fieldsets = (
        (_('Información del documento'), {
            'fields': ('claim', 'document_name', 'document_type', 'file', 'is_required')
        }),
        (_('Información del sistema'), {
            'fields': ('file_size', 'uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('file_size', 'uploaded_at')

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related(
            'claim', 'uploaded_by'
        )

@admin.register(ClaimTimeline)
class ClaimTimelineAdmin(admin.ModelAdmin):
    """
    Admin configuration for ClaimTimeline model
    """
    list_display = ('claim', 'event_type', 'event_description', 'old_status', 'new_status', 'created_by', 'created_at')
    list_filter = ('event_type', 'created_at', 'created_by')
    search_fields = ('claim__claim_number', 'event_description', 'created_by__username')
    ordering = ('-created_at',)
    raw_id_fields = ('claim', 'created_by')

    fieldsets = (
        (_('Información del evento'), {
            'fields': ('claim', 'event_type', 'event_description')
        }),
        (_('Estados'), {
            'fields': ('old_status', 'new_status'),
            'classes': ('collapse',)
        }),
        (_('Información del sistema'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at',)
