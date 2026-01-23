import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from audit.models import AuditLog

from .forms import (
    InvoiceBulkActionForm,
    InvoiceForm,
    InvoicePaymentForm,
    InvoiceSearchForm,
)
from .models import Invoice


@login_required
def invoice_list(request):
    """List all invoices with search and filtering"""
    search_form = InvoiceSearchForm(request.GET)
    invoices = (
        Invoice.objects.all()
        .select_related("policy__insurance_company", "policy__broker", "created_by")
        .order_by("-created_at")
    )

    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        payment_status = search_form.cleaned_data.get("payment_status")
        policy = search_form.cleaned_data.get("policy")
        date_from = search_form.cleaned_data.get("date_from")
        date_to = search_form.cleaned_data.get("date_to")
        created_by = search_form.cleaned_data.get("created_by")
        overdue = search_form.cleaned_data.get("overdue")

        if search:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search)
                | Q(policy__policy_number__icontains=search)
                | Q(policy__insurance_company__name__icontains=search)
            )

        if payment_status:
            invoices = invoices.filter(payment_status=payment_status)

        if policy:
            invoices = invoices.filter(policy=policy)

        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)

        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)

        if created_by:
            invoices = invoices.filter(created_by=created_by)

        if overdue:
            today = timezone.now().date()
            invoices = invoices.filter(payment_status="pending", due_date__lt=today)

    # Pagination
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(total=Sum("total_amount"))["total"] or 0

    paid_amount = (
        invoices.filter(payment_status="paid").aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )

    pending_amount = (
        invoices.filter(payment_status="pending").aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
    }

    return render(request, "invoices/invoice_list.html", context)


@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "policy__insurance_company", "policy__broker", "created_by"
        ),
        pk=pk,
    )

    # Check permissions
    if not request.user.has_role_permission("invoices_read"):
        # If user doesn't have general read permission, check if they're the creator or responsible for the policy
        if (
            request.user != invoice.created_by
            and request.user != invoice.policy.responsible_user
        ):
            messages.error(request, _("No tienes permisos para ver esta factura."))
            return redirect("invoices:invoice_list")

    context = {
        "invoice": invoice,
        "is_overdue": invoice.payment_status == "pending"
        and invoice.due_date < timezone.now().date(),
        "days_overdue": (
            (timezone.now().date() - invoice.due_date).days
            if invoice.due_date < timezone.now().date()
            else 0
        ),
    }

    return render(request, "invoices/invoice_detail.html", context)


@login_required
@permission_required("invoices.invoices_create", raise_exception=True)
def invoice_create(request):
    """Create new invoice"""
    if request.method == "POST":
        form = InvoiceForm(request.POST, user=request.user)
        if form.is_valid():
            invoice = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="create",
                entity_type="invoice",
                entity_id=str(invoice.id),
                description=f"Factura creada: {invoice.invoice_number}",
                new_values={
                    "invoice_number": invoice.invoice_number,
                    "policy": invoice.policy.policy_number,
                    "total_amount": str(invoice.total_amount),
                    "due_date": str(invoice.due_date),
                },
            )

            messages.success(request, _("Factura creada exitosamente."))
            return redirect("invoices:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(user=request.user)

    return render(
        request,
        "invoices/invoice_form.html",
        {
            "form": form,
            "title": _("Crear Nueva Factura"),
            "submit_text": _("Crear Factura"),
        },
    )


@login_required
@permission_required("invoices.invoices_write", raise_exception=True)
def invoice_edit(request, pk):
    """Edit existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Only allow editing if not paid
    if invoice.payment_status == "paid":
        messages.error(
            request, _("No se pueden editar facturas que ya han sido pagadas.")
        )
        return redirect("invoices:invoice_detail", pk=pk)

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        if form.is_valid():
            old_values = {
                "policy": invoice.policy.policy_number,
                "invoice_date": str(invoice.invoice_date),
                "due_date": str(invoice.due_date),
                "total_amount": str(invoice.total_amount),
            }

            updated_invoice = form.save()

            new_values = {
                "policy": updated_invoice.policy.policy_number,
                "invoice_date": str(updated_invoice.invoice_date),
                "due_date": str(updated_invoice.due_date),
                "total_amount": str(updated_invoice.total_amount),
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="update",
                entity_type="invoice",
                entity_id=str(updated_invoice.id),
                description=f"Factura actualizada: {updated_invoice.invoice_number}",
                old_values=old_values,
                new_values=new_values,
            )

            messages.success(request, _("Factura actualizada exitosamente."))
            return redirect("invoices:invoice_detail", pk=updated_invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, user=request.user)

    return render(
        request,
        "invoices/invoice_form.html",
        {
            "form": form,
            "invoice": invoice,
            "title": _("Editar Factura"),
            "submit_text": _("Actualizar Factura"),
        },
    )


@login_required
@permission_required("invoices.invoices_write", raise_exception=True)
def invoice_mark_paid(request, pk):
    """Mark invoice as paid"""
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.payment_status == "paid":
        messages.warning(request, _("Esta factura ya está marcada como pagada."))
        return redirect("invoices:invoice_detail", pk=pk)

    if request.method == "POST":
        form = InvoicePaymentForm(request.POST, instance=invoice)
        if form.is_valid():
            old_status = invoice.payment_status
            updated_invoice = form.save()
            updated_invoice.payment_status = "paid"
            updated_invoice.save()

            # Apply early payment discount if applicable
            updated_invoice.apply_early_payment_discount()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="payment",
                entity_type="invoice",
                entity_id=str(updated_invoice.id),
                description=f"Factura pagada: {updated_invoice.invoice_number}",
                old_values={"payment_status": old_status, "payment_date": None},
                new_values={
                    "payment_status": "paid",
                    "payment_date": str(updated_invoice.payment_date),
                },
            )

            messages.success(request, _("Factura marcada como pagada exitosamente."))
            return redirect("invoices:invoice_detail", pk=updated_invoice.pk)
    else:
        form = InvoicePaymentForm(instance=invoice)

    return render(
        request,
        "invoices/invoice_mark_paid.html",
        {
            "form": form,
            "invoice": invoice,
        },
    )


@login_required
@permission_required("invoices.invoices_delete", raise_exception=True)
def invoice_delete(request, pk):
    """Soft delete invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Don't allow deleting paid invoices
    if invoice.payment_status == "paid":
        messages.error(
            request, _("No se pueden eliminar facturas que ya han sido pagadas.")
        )
        return redirect("invoices:invoice_detail", pk=pk)

    invoice_number = invoice.invoice_number
    invoice.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="delete",
        entity_type="invoice",
        entity_id=str(pk),
        description=f"Factura eliminada: {invoice_number}",
    )

    messages.success(request, _("Factura eliminada exitosamente."))
    return redirect("invoices:invoice_list")


@login_required
def invoice_pdf(request, pk):
    """Generate invoice PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Check permissions
    if not request.user.has_role_permission("invoices_read"):
        if (
            request.user != invoice.created_by
            and request.user != invoice.policy.responsible_user
        ):
            messages.error(request, _("No tienes permisos para ver esta factura."))
            return redirect("invoices:invoice_list")

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="export",
        entity_type="invoice",
        entity_id=str(invoice.id),
        description=f"PDF generado: {invoice.invoice_number}",
    )

    # For now, just return a placeholder message
    messages.info(
        request,
        _("Funcionalidad de PDF en desarrollo. Por ahora puede imprimir la página."),
    )
    return redirect("invoices:invoice_detail", pk=pk)


@require_POST
@login_required
@permission_required("invoices.invoices_write", raise_exception=True)
def invoice_bulk_action(request):
    """Handle bulk actions on invoices"""
    form = InvoiceBulkActionForm(request.POST)

    if not form.is_valid():
        messages.error(request, _("Datos inválidos."))
        return redirect("invoices:invoice_list")

    action = form.cleaned_data["action"]
    invoice_ids = request.POST.getlist("invoice_ids")

    if not invoice_ids:
        messages.error(request, _("No se seleccionaron facturas."))
        return redirect("invoices:invoice_list")

    invoices = Invoice.objects.filter(id__in=invoice_ids)

    if action == "mark_paid":
        payment_date = form.cleaned_data["payment_date"]
        updated_count = 0

        for invoice in invoices:
            if invoice.payment_status != "paid":
                invoice.payment_status = "paid"
                invoice.payment_date = payment_date
                invoice.apply_early_payment_discount()
                invoice.save()
                updated_count += 1

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type="payment",
                    entity_type="invoice",
                    entity_id=str(invoice.id),
                    description=f"Factura pagada (bulk): {invoice.invoice_number}",
                )

        if updated_count > 0:
            messages.success(
                request, f"{updated_count} facturas marcadas como pagadas."
            )
        else:
            messages.warning(
                request, _("Todas las facturas seleccionadas ya estaban pagadas.")
            )

    elif action == "export":
        # Placeholder for export functionality
        messages.info(request, _("Funcionalidad de exportación en desarrollo."))

    return redirect("invoices:invoice_list")
