from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import UserProfile


class Report(models.Model):
    """
    Model for saved reports
    """

    REPORT_TYPES = [
        ("policies_summary", _("Resumen de Pólizas")),
        ("policies_expiring", _("Pólizas por Vencer")),
        ("claims_summary", _("Resumen de Siniestros")),
        ("claims_by_cause", _("Siniestros por Causa")),
        ("financial_summary", _("Resumen Financiero")),
        ("assets_summary", _("Resumen de Bienes")),
        ("performance_metrics", _("Métricas de Rendimiento")),
    ]

    EXPORT_FORMATS = [
        ("html", _("HTML")),
        ("pdf", _("PDF")),
        ("excel", _("Excel")),
        ("csv", _("CSV")),
    ]

    name = models.CharField(_("Nombre del Reporte"), max_length=255)
    report_type = models.CharField(
        _("Tipo de Reporte"), max_length=50, choices=REPORT_TYPES
    )
    description = models.TextField(_("Descripción"), blank=True)

    # Filters and parameters (stored as JSON)
    filters = models.JSONField(_("Filtros"), default=dict, blank=True)
    parameters = models.JSONField(_("Parámetros"), default=dict, blank=True)

    # Scheduling
    is_scheduled = models.BooleanField(_("Programado"), default=False)
    schedule_frequency = models.CharField(
        _("Frecuencia"),
        max_length=20,
        choices=[
            ("daily", _("Diario")),
            ("weekly", _("Semanal")),
            ("monthly", _("Mensual")),
        ],
        blank=True,
    )

    # Recipients for scheduled reports
    recipients = models.ManyToManyField(
        UserProfile,
        verbose_name=_("Destinatarios"),
        related_name="scheduled_reports",
        blank=True,
    )

    # Metadata
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Creado por"),
        related_name="created_reports",
    )
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de actualización"), auto_now=True)
    last_run = models.DateTimeField(_("Última ejecución"), null=True, blank=True)

    class Meta:
        verbose_name = _("Reporte")
        verbose_name_plural = _("Reportes")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_report_data(self):
        """
        Generate report data based on type and filters
        """
        from datetime import timedelta

        from django.db.models import Avg, Count, Sum
        from django.utils import timezone

        from assets.models import Asset
        from claims.models import Claim
        from invoices.models import Invoice
        from policies.models import Policy

        data = {
            "report_type": self.report_type,
            "generated_at": timezone.now(),
            "filters": self.filters,
            "data": {},
        }

        if self.report_type == "policies_summary":
            # Policies summary report
            total_policies = Policy.objects.count()
            active_policies = Policy.objects.filter(status="active").count()
            expired_policies = Policy.objects.filter(status="expired").count()
            expiring_30_days = Policy.objects.filter(
                end_date__lte=timezone.now().date() + timedelta(days=30),
                end_date__gte=timezone.now().date(),
                status="active",
            ).count()

            total_insured_value = (
                Policy.objects.filter(status="active").aggregate(
                    total=Sum("insured_value")
                )["total"]
                or 0
            )

            data["data"] = {
                "total_policies": total_policies,
                "active_policies": active_policies,
                "expired_policies": expired_policies,
                "expiring_30_days": expiring_30_days,
                "total_insured_value": total_insured_value,
            }

        elif self.report_type == "policies_expiring":
            # Expiring policies report
            days_ahead = self.parameters.get("days_ahead", 30)
            expiring_policies = Policy.objects.filter(
                end_date__lte=timezone.now().date() + timedelta(days=days_ahead),
                end_date__gte=timezone.now().date(),
                status="active",
            ).select_related("insurance_company", "responsible_user")

            data["data"] = {
                "policies": list(
                    expiring_policies.values(
                        "policy_number",
                        "insurance_company__name",
                        "end_date",
                        "insured_value",
                        "responsible_user__username",
                    )
                ),
                "total_count": expiring_policies.count(),
            }

        elif self.report_type == "claims_summary":
            # Claims summary report
            total_claims = Claim.objects.count()
            open_claims = Claim.objects.filter(
                status__in=[
                    "reported",
                    "documentation_pending",
                    "sent_to_insurer",
                    "under_evaluation",
                ]
            ).count()
            closed_claims = Claim.objects.filter(
                status__in=["closed", "paid", "rejected"]
            ).count()
            paid_claims = Claim.objects.filter(status="paid").count()

            claims_by_status = Claim.objects.values("status").annotate(
                count=Count("id")
            )
            claims_by_cause = (
                Claim.objects.values("incident_description")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )

            total_paid_amount = (
                Claim.objects.filter(status="paid").aggregate(
                    total=Sum("approved_amount")
                )["total"]
                or 0
            )

            data["data"] = {
                "total_claims": total_claims,
                "open_claims": open_claims,
                "closed_claims": closed_claims,
                "paid_claims": paid_claims,
                "claims_by_status": list(claims_by_status),
                "claims_by_cause": list(claims_by_cause),
                "total_paid_amount": total_paid_amount,
            }

        elif self.report_type == "financial_summary":
            # Financial summary report
            total_invoices = Invoice.objects.count()
            paid_invoices = Invoice.objects.filter(payment_status="paid").count()
            pending_invoices = Invoice.objects.filter(payment_status="pending").count()
            overdue_invoices = Invoice.objects.filter(
                payment_status="pending", due_date__lt=timezone.now().date()
            ).count()

            total_revenue = (
                Invoice.objects.filter(payment_status="paid").aggregate(
                    total=Sum("total_amount")
                )["total"]
                or 0
            )

            pending_amount = (
                Invoice.objects.filter(payment_status="pending").aggregate(
                    total=Sum("total_amount")
                )["total"]
                or 0
            )

            monthly_revenue = (
                Invoice.objects.filter(
                    payment_status="paid",
                    payment_date__year=timezone.now().year,
                    payment_date__month=timezone.now().month,
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            data["data"] = {
                "total_invoices": total_invoices,
                "paid_invoices": paid_invoices,
                "pending_invoices": pending_invoices,
                "overdue_invoices": overdue_invoices,
                "total_revenue": total_revenue,
                "pending_amount": pending_amount,
                "monthly_revenue": monthly_revenue,
            }

        elif self.report_type == "performance_metrics":
            # Performance metrics report
            avg_resolution_time = (
                Claim.objects.filter(status__in=["closed", "paid"])
                .exclude(created_at__isnull=True)
                .aggregate(
                    avg_days=Avg(
                        models.functions.DateDiff(
                            models.functions.TruncDate("updated_at"),
                            models.functions.TruncDate("created_at"),
                        )
                    )
                )["avg_days"]
                or 0
            )

            claims_resolution_rate = 0
            if Claim.objects.count() > 0:
                resolved_claims = Claim.objects.filter(
                    status__in=["closed", "paid"]
                ).count()
                claims_resolution_rate = (resolved_claims / Claim.objects.count()) * 100

            policy_utilization = 0
            if Policy.objects.count() > 0:
                active_policies = Policy.objects.filter(status="active").count()
                policy_utilization = (active_policies / Policy.objects.count()) * 100

            data["data"] = {
                "avg_resolution_time_days": round(avg_resolution_time, 1),
                "claims_resolution_rate_percent": round(claims_resolution_rate, 1),
                "policy_utilization_percent": round(policy_utilization, 1),
                "total_active_policies": Policy.objects.filter(status="active").count(),
                "total_open_claims": Claim.objects.filter(
                    status__in=[
                        "reported",
                        "documentation_pending",
                        "sent_to_insurer",
                        "under_evaluation",
                    ]
                ).count(),
            }

        return data


class ReportExecution(models.Model):
    """
    Model for report execution logs
    """

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        verbose_name=_("Reporte"),
        related_name="executions",
    )
    executed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Ejecutado por"),
        related_name="report_executions",
    )
    executed_at = models.DateTimeField(_("Fecha de ejecución"), auto_now_add=True)
    execution_time_seconds = models.FloatField(_("Tiempo de ejecución (segundos)"))
    success = models.BooleanField(_("Éxito"), default=True)
    error_message = models.TextField(_("Mensaje de error"), blank=True)

    # Export information
    export_format = models.CharField(
        _("Formato de exportación"),
        max_length=10,
        choices=Report.EXPORT_FORMATS,
        blank=True,
    )
    exported_file = models.FileField(
        _("Archivo exportado"),
        upload_to="reports/exports/%Y/%m/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Ejecución de Reporte")
        verbose_name_plural = _("Ejecuciones de Reportes")
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.report.name} - {self.executed_at.date()}"
