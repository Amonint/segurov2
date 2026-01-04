from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Policy, PolicyDocument

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    """
    Admin configuration for Policy model
    """
    list_display = ('policy_number', 'insurance_company', 'group_type', 'insured_value', 'start_date', 'end_date', 'status', 'responsible_user')
    list_filter = ('status', 'group_type', 'insurance_company', 'broker', 'start_date', 'end_date', 'created_at')
    search_fields = ('policy_number', 'insurance_company__name', 'subgroup', 'branch', 'responsible_user__username')
    ordering = ('-created_at',)
    raw_id_fields = ('insurance_company', 'broker', 'responsible_user')

    fieldsets = (
        (_('Información básica'), {
            'fields': ('policy_number', 'insurance_company', 'broker', 'responsible_user')
        }),
        (_('Clasificación'), {
            'fields': ('group_type', 'subgroup', 'branch')
        }),
        (_('Fechas'), {
            'fields': ('start_date', 'end_date', 'issue_date')
        }),
        (_('Información financiera'), {
            'fields': ('insured_value',)
        }),
        (_('Descripciones'), {
            'fields': ('coverage_description', 'observations'),
            'classes': ('collapse',)
        }),
        (_('Estado'), {
            'fields': ('status',)
        }),
        (_('Fechas del sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return super().get_queryset(request).select_related(
            'insurance_company', 'broker', 'responsible_user'
        )

@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    """
    Admin configuration for PolicyDocument model
    """
    list_display = ('document_name', 'policy', 'document_type', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('document_name', 'policy__policy_number', 'uploaded_by__username')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('policy', 'uploaded_by')

    fieldsets = (
        (_('Información del documento'), {
            'fields': ('policy', 'document_name', 'document_type', 'file')
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
            'policy', 'uploaded_by'
        )
