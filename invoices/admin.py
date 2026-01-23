from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Invoice model
    """

    list_display = (
        "invoice_number",
        "policy",
        "invoice_date",
        "due_date",
        "total_amount",
        "payment_status",
        "created_by",
    )
    list_filter = (
        "payment_status",
        "invoice_date",
        "due_date",
        "created_at",
        "created_by",
    )
    search_fields = (
        "invoice_number",
        "policy__policy_number",
        "policy__insurance_company__name",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("policy", "created_by")

    fieldsets = (
        (
            _("Información básica"),
            {
                "fields": (
                    "policy",
                    "invoice_number",
                    "invoice_date",
                    "due_date",
                    "created_by",
                )
            },
        ),
        (
            _("Cálculos automáticos"),
            {
                "fields": (
                    "premium",
                    "superintendence_contribution",
                    "farm_insurance_contribution",
                    "emission_rights",
                    "tax_base",
                    "iva",
                    "withholding_tax",
                    "early_payment_discount",
                    "total_amount",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Estado de pago"), {"fields": ("payment_status", "payment_date")}),
        (
            _("Fechas del sistema"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = (
        "invoice_number",
        "premium",
        "superintendence_contribution",
        "farm_insurance_contribution",
        "emission_rights",
        "tax_base",
        "iva",
        "early_payment_discount",
        "total_amount",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        return (
            super()
            .get_queryset(request)
            .select_related("policy", "policy__insurance_company", "created_by")
        )

    def has_add_permission(self, request):
        """
        Only allow adding invoices through the system, not directly in admin
        """
        return False
