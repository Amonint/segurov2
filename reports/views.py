import json
import time
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from audit.models import AuditLog
from claims.models import Claim
from invoices.models import Invoice
from policies.models import Policy

from .forms import QuickReportForm, ReportExecutionForm, ReportFilterForm, ReportForm
from .models import Report, ReportExecution


@login_required
def report_list(request):
    """List all saved reports"""
    reports = Report.objects.all().order_by("-created_at")
    paginator = Paginator(reports, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_reports": reports.count(),
    }

    return render(request, "reports/report_list.html", context)


@login_required
@permission_required("reports.reports_create", raise_exception=True)
def report_create(request):
    """Create new saved report"""
    if request.method == "POST":
        form = ReportForm(request.POST, user=request.user)
        if form.is_valid():
            report = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="create",
                entity_type="report",
                entity_id=str(report.id),
                description=f"Reporte creado: {report.name}",
                new_values={
                    "name": report.name,
                    "report_type": report.report_type,
                    "is_scheduled": report.is_scheduled,
                },
            )

            messages.success(request, _("Reporte creado exitosamente."))
            return redirect("reports:report_detail", pk=report.pk)
    else:
        form = ReportForm(user=request.user)

    return render(
        request,
        "reports/report_form.html",
        {
            "form": form,
            "title": _("Crear Nuevo Reporte"),
            "submit_text": _("Crear Reporte"),
        },
    )


@login_required
def report_detail(request, pk):
    """View report details and execution history"""
    report = get_object_or_404(Report, pk=pk)

    # Check permissions
    if (
        not request.user.has_role_permission("reports_read")
        and report.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para ver este reporte."))
        return redirect("reports:report_list")

    # Get execution history
    executions = report.executions.all()[:10]  # Last 10 executions

    context = {
        "report": report,
        "executions": executions,
        "can_edit": request.user.has_role_permission("reports_write")
        or report.created_by == request.user,
        "can_execute": request.user.has_role_permission("reports_execute")
        or report.created_by == request.user,
    }

    return render(request, "reports/report_detail.html", context)


@login_required
@permission_required("reports.reports_write", raise_exception=True)
def report_edit(request, pk):
    """Edit existing report"""
    report = get_object_or_404(Report, pk=pk)

    # Check ownership
    if (
        not request.user.has_role_permission("reports_write")
        and report.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para editar este reporte."))
        return redirect("reports:report_detail", pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST, instance=report, user=request.user)
        if form.is_valid():
            old_values = {
                "name": report.name,
                "report_type": report.report_type,
                "is_scheduled": report.is_scheduled,
                "schedule_frequency": report.schedule_frequency,
            }

            updated_report = form.save()

            new_values = {
                "name": updated_report.name,
                "report_type": updated_report.report_type,
                "is_scheduled": updated_report.is_scheduled,
                "schedule_frequency": updated_report.schedule_frequency,
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="update",
                entity_type="report",
                entity_id=str(updated_report.id),
                description=f"Reporte actualizado: {updated_report.name}",
                old_values=old_values,
                new_values=new_values,
            )

            messages.success(request, _("Reporte actualizado exitosamente."))
            return redirect("reports:report_detail", pk=updated_report.pk)
    else:
        form = ReportForm(instance=report, user=request.user)

    return render(
        request,
        "reports/report_form.html",
        {
            "form": form,
            "report": report,
            "title": _("Editar Reporte"),
            "submit_text": _("Actualizar Reporte"),
        },
    )


@login_required
@permission_required("reports.reports_delete", raise_exception=True)
def report_delete(request, pk):
    """Delete report"""
    report = get_object_or_404(Report, pk=pk)

    # Check ownership
    if (
        not request.user.has_role_permission("reports_delete")
        and report.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para eliminar este reporte."))
        return redirect("reports:report_detail", pk=pk)

    report_name = report.name
    report.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="delete",
        entity_type="report",
        entity_id=str(pk),
        description=f"Reporte eliminado: {report_name}",
    )

    messages.success(request, _("Reporte eliminado exitosamente."))
    return redirect("reports:report_list")


@login_required
def report_execute(request, pk):
    """Execute a saved report"""
    report = get_object_or_404(Report, pk=pk)

    # Check permissions
    if (
        not request.user.has_role_permission("reports_execute")
        and report.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para ejecutar este reporte."))
        return redirect("reports:report_detail", pk=pk)

    if request.method == "POST":
        form = ReportExecutionForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data["export_format"]
            override_filters = form.cleaned_data.get("override_filters", False)

            # Record execution start time
            start_time = time.time()

            try:
                # Generate report data
                report_data = report.get_report_data()

                # Apply override filters if specified
                if override_filters:
                    date_from = form.cleaned_data.get("date_from")
                    date_to = form.cleaned_data.get("date_to")
                    if date_from and date_to:
                        report_data["filters"]["date_from"] = str(date_from)
                        report_data["filters"]["date_to"] = str(date_to)

                # Calculate execution time
                execution_time = time.time() - start_time

                # Create execution record
                execution = ReportExecution.objects.create(
                    report=report,
                    executed_by=request.user,
                    execution_time_seconds=execution_time,
                    success=True,
                    export_format=export_format,
                )

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type="export",
                    entity_type="report",
                    entity_id=str(report.id),
                    description=f"Reporte ejecutado: {report.name} ({export_format})",
                )

                # Handle different export formats
                if export_format == "html":
                    return render(
                        request,
                        "reports/report_view.html",
                        {
                            "report": report,
                            "report_data": report_data,
                            "execution": execution,
                        },
                    )
                elif export_format == "pdf":
                    return generate_pdf_report(request, report, report_data)
                elif export_format == "excel":
                    return generate_excel_report(request, report, report_data)
                elif export_format == "csv":
                    return generate_csv_report(request, report, report_data)

            except Exception as e:
                # Record failed execution
                execution_time = time.time() - start_time
                ReportExecution.objects.create(
                    report=report,
                    executed_by=request.user,
                    execution_time_seconds=execution_time,
                    success=False,
                    error_message=str(e),
                )

                messages.error(request, f"Error al generar el reporte: {str(e)}")
                return redirect("reports:report_detail", pk=pk)
    else:
        form = ReportExecutionForm()

    return render(
        request,
        "reports/report_execute.html",
        {
            "form": form,
            "report": report,
        },
    )


@login_required
def quick_report(request):
    """Generate quick reports without saving"""
    if request.method == "POST":
        form = QuickReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data["report_type"]
            export_format = form.cleaned_data["export_format"]

            # Create temporary report object
            temp_report = Report(
                name=f"Reporte Rápido - {dict(Report.REPORT_TYPES)[report_type]}",
                report_type=report_type,
                created_by=request.user,
            )

            # Set filters based on form data
            date_range = form.cleaned_data.get("date_range")
            custom_date_from = form.cleaned_data.get("custom_date_from")
            custom_date_to = form.cleaned_data.get("custom_date_to")

            filters = {}
            if date_range:
                filters["date_range"] = date_range
            if custom_date_from and custom_date_to:
                filters["date_from"] = str(custom_date_from)
                filters["date_to"] = str(custom_date_to)

            temp_report.filters = filters

            try:
                # Generate report data
                report_data = temp_report.get_report_data()

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type="export",
                    entity_type="report",
                    entity_id="0",  # Temporary report
                    description=f"Reporte rápido generado: {dict(Report.REPORT_TYPES)[report_type]} ({export_format})",
                )

                # Handle export formats
                if export_format == "html":
                    return render(
                        request,
                        "reports/quick_report_view.html",
                        {
                            "report_type": report_type,
                            "report_data": report_data,
                            "generated_at": timezone.now(),
                        },
                    )
                elif export_format == "pdf":
                    return generate_pdf_report(request, temp_report, report_data)
                elif export_format == "excel":
                    return generate_excel_report(request, temp_report, report_data)
                elif export_format == "csv":
                    return generate_csv_report(request, temp_report, report_data)

            except Exception as e:
                messages.error(request, f"Error al generar el reporte: {str(e)}")
    elif request.method == "GET" and request.GET.get("report_type"):
        # Handle direct GET request with report_type parameter
        report_type = request.GET.get("report_type")
        export_format = request.GET.get("export_format", "html")  # Default to html

        # Validate report_type
        valid_types = [choice[0] for choice in Report.REPORT_TYPES]
        if report_type not in valid_types:
            messages.error(request, f"Tipo de reporte inválido: {report_type}")
            return redirect("reports:quick_report")

        # Create temporary report object
        temp_report = Report(
            name=f"Reporte Rápido - {dict(Report.REPORT_TYPES)[report_type]}",
            report_type=report_type,
            created_by=request.user,
        )

        # Set default filters or from GET params
        filters = {}
        date_range = request.GET.get("date_range")
        if date_range:
            filters["date_range"] = date_range

        temp_report.filters = filters

        try:
            # Generate report data
            report_data = temp_report.get_report_data()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="export",
                entity_type="report",
                entity_id="0",  # Temporary report
                description=f"Reporte rápido generado: {dict(Report.REPORT_TYPES)[report_type]} ({export_format})",
            )

            # Handle export formats
            if export_format == "html":
                return render(
                    request,
                    "reports/quick_report_view.html",
                    {
                        "report_type": report_type,
                        "report_data": report_data,
                        "generated_at": timezone.now(),
                    },
                )
            elif export_format == "pdf":
                return generate_pdf_report(request, temp_report, report_data)
            elif export_format == "excel":
                return generate_excel_report(request, temp_report, report_data)
            elif export_format == "csv":
                return generate_csv_report(request, temp_report, report_data)

        except Exception as e:
            messages.error(request, f"Error al generar el reporte: {str(e)}")
            return redirect("reports:quick_report")

    # Show form for GET without parameters or invalid cases
    form = QuickReportForm()
    return render(
        request,
        "reports/quick_report.html",
        {
            "form": form,
        },
    )


@login_required
def dashboard_reports(request):
    """Dashboard with key reports and metrics"""
    # Generate key metrics
    from assets.models import Asset
    from claims.models import Claim
    from invoices.models import Invoice
    from policies.models import Policy

    # Policies metrics
    total_policies = Policy.objects.count()
    active_policies = Policy.objects.filter(status="active").count()
    expiring_30_days = Policy.objects.filter(
        end_date__lte=timezone.now().date() + timedelta(days=30),
        end_date__gte=timezone.now().date(),
        status="active",
    ).count()

    # Claims metrics
    total_claims = Claim.objects.count()
    open_claims = Claim.objects.filter(
        status__in=[
            "reported",
            "documentation_pending",
            "sent_to_insurer",
            "under_evaluation",
        ]
    ).count()
    paid_claims = Claim.objects.filter(status="paid").count()

    # Financial metrics
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

    # Assets metrics
    total_assets = Asset.objects.count()
    insured_assets = Asset.objects.filter(is_insured=True).count()

    context = {
        "metrics": {
            "policies": {
                "total": total_policies,
                "active": active_policies,
                "expiring_30_days": expiring_30_days,
            },
            "claims": {
                "total": total_claims,
                "open": open_claims,
                "paid": paid_claims,
            },
            "financial": {
                "total_revenue": total_revenue,
                "pending_amount": pending_amount,
            },
            "assets": {
                "total": total_assets,
                "insured": insured_assets,
            },
        }
    }

    return render(request, "reports/dashboard.html", context)


# Legacy report functions (keeping for compatibility)
@login_required
def policies_report(request):
    """Policies report (legacy)"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    policies = Policy.objects.filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    )

    # Aggregate data
    total_policies = policies.count()
    active_policies = policies.filter(status="active").count()
    expired_policies = policies.filter(status="expired").count()

    # Group by insurance company
    company_stats = (
        policies.values("insurance_company__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "total_policies": total_policies,
        "active_policies": active_policies,
        "expired_policies": expired_policies,
        "company_stats": company_stats,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reports/policies_report.html", context)


@login_required
def claims_report(request):
    """Claims report (legacy)"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    claims = Claim.objects.filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    )

    # Aggregate data
    total_claims = claims.count()
    status_stats = claims.values("status").annotate(count=Count("id"))

    # Calculate total estimated loss
    total_estimated_loss = claims.aggregate(total=Sum("estimated_loss"))["total"] or 0

    context = {
        "total_claims": total_claims,
        "status_stats": status_stats,
        "total_estimated_loss": total_estimated_loss,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reports/claims_report.html", context)


@login_required
def invoices_report(request):
    """Invoices report (legacy)"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    )

    # Aggregate data
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(payment_status="paid").count()
    pending_invoices = invoices.filter(payment_status="pending").count()
    total_amount = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
    paid_amount = (
        invoices.filter(payment_status="paid").aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )

    context = {
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "pending_invoices": pending_invoices,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": total_amount - paid_amount,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reports/invoices_report.html", context)


@login_required
def financial_report(request):
    """Financial summary report (legacy)"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # Last 3 months

    # Revenue data
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    )

    from django.db.models.functions import TruncMonth

    monthly_revenue = (
        invoices.filter(payment_status="paid")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    # Outstanding payments
    outstanding_invoices = Invoice.objects.filter(payment_status="pending")
    total_outstanding = (
        outstanding_invoices.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    context = {
        "monthly_revenue": monthly_revenue,
        "total_outstanding": total_outstanding,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reports/financial_report.html", context)


def generate_pdf_report(request, report, report_data):
    """Generate PDF report (placeholder)"""
    # This would require a PDF library like reportlab or weasyprint
    messages.info(request, _("Funcionalidad de PDF en desarrollo. Use HTML por ahora."))
    return redirect("reports:report_list")


def generate_excel_report(request, report, report_data):
    """Generate Excel report (placeholder)"""
    # This would require openpyxl or similar
    messages.info(
        request, _("Funcionalidad de Excel en desarrollo. Use HTML por ahora.")
    )
    return redirect("reports:report_list")


def generate_csv_report(request, report, report_data):
    """Generate CSV report (placeholder)"""
    # This would create a CSV file
    messages.info(request, _("Funcionalidad de CSV en desarrollo. Use HTML por ahora."))
    return redirect("reports:report_list")


@login_required
def export_policies_report(request):
    """Export policies report to Excel (legacy)"""
    messages.info(request, _("Funcionalidad de exportación en desarrollo"))
    return redirect("reports:policies_report")


@login_required
def export_claims_report(request):
    """Export claims report to Excel (legacy)"""
    messages.info(request, _("Funcionalidad de exportación en desarrollo"))
    return redirect("reports:claims_report")


@login_required
def export_financial_report(request):
    """Export financial report to Excel (legacy)"""
    messages.info(request, _("Funcionalidad de exportación en desarrollo"))
    return redirect("reports:financial_report")
