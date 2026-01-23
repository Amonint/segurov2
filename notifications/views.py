from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.models import UserProfile
from audit.models import AuditLog

from .email_service import EmailService
from .forms import AlertForm, EmailTemplateForm
from .models import Alert, EmailLog, EmailTemplate, Notification
from .tasks import run_scheduled_alerts


@login_required
def email_templates_list(request):
    """List all email templates"""
    if not request.user.get_role_permissions().__contains__("settings_read"):
        messages.error(request, _("No tienes permisos para ver plantillas de email."))
        return redirect("accounts:dashboard")

    templates = EmailTemplate.objects.all().order_by("template_type", "name")

    return render(
        request,
        "notifications/email_templates_list.html",
        {
            "templates": templates,
            "title": _("Plantillas de Email"),
        },
    )


@login_required
def email_templates_create(request):
    """Create new email template"""
    if not request.user.get_role_permissions().__contains__("settings_write"):
        messages.error(request, _("No tienes permisos para crear plantillas de email."))
        return redirect("notifications:email_templates_list")

    if request.method == "POST":
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, _("Plantilla de email creada exitosamente."))
            return redirect("notifications:email_templates_list")
    else:
        form = EmailTemplateForm()

    return render(
        request,
        "notifications/email_templates_form.html",
        {
            "form": form,
            "title": _("Crear Plantilla de Email"),
            "submit_text": _("Crear"),
        },
    )


@login_required
def email_templates_edit(request, pk):
    """Edit email template"""
    if not request.user.get_role_permissions().__contains__("settings_write"):
        messages.error(
            request, _("No tienes permisos para editar plantillas de email.")
        )
        return redirect("notifications:email_templates_list")

    template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _("Plantilla de email actualizada exitosamente."))
            return redirect("notifications:email_templates_list")
    else:
        form = EmailTemplateForm(instance=template)

    return render(
        request,
        "notifications/email_templates_form.html",
        {
            "form": form,
            "title": _("Editar Plantilla de Email"),
            "submit_text": _("Actualizar"),
            "template": template,
        },
    )


@login_required
def email_logs_list(request):
    """List email logs"""
    if not request.user.get_role_permissions().__contains__("settings_read"):
        messages.error(request, _("No tienes permisos para ver logs de email."))
        return redirect("accounts:dashboard")

    # Get filter parameters
    status = request.GET.get("status", "")
    template_type = request.GET.get("template_type", "")
    search = request.GET.get("search", "")

    # Base queryset
    queryset = EmailLog.objects.select_related(
        "template", "claim", "policy", "invoice", "created_by"
    ).order_by("-created_at")

    # Apply filters
    if status:
        queryset = queryset.filter(status=status)
    if template_type:
        queryset = queryset.filter(template__template_type=template_type)
    if search:
        queryset = queryset.filter(
            Q(recipient_email__icontains=search)
            | Q(subject__icontains=search)
            | Q(recipient_name__icontains=search)
        )

    logs = queryset[:100]  # Limit to last 100 emails

    # Get stats
    stats = EmailService.get_email_stats()

    return render(
        request,
        "notifications/email_logs_list.html",
        {
            "logs": logs,
            "stats": stats,
            "status_filter": status,
            "template_type_filter": template_type,
            "search": search,
            "title": _("Logs de Email"),
        },
    )


@login_required
def email_logs_detail(request, pk):
    """View email log detail"""
    if not request.user.get_role_permissions().__contains__("settings_read"):
        messages.error(request, _("No tienes permisos para ver detalles de email."))
        return redirect("notifications:email_logs_list")

    log = get_object_or_404(
        EmailLog.objects.select_related(
            "template", "claim", "policy", "invoice", "created_by"
        ),
        pk=pk,
    )

    return render(
        request,
        "notifications/email_logs_detail.html",
        {
            "log": log,
            "title": _("Detalle de Email"),
        },
    )


@login_required
def test_email_template(request, pk):
    """Test email template with sample data"""
    if not request.user.get_role_permissions().__contains__("settings_write"):
        messages.error(
            request, _("No tienes permisos para probar plantillas de email.")
        )
        return redirect("notifications:email_templates_list")

    template = get_object_or_404(EmailTemplate, pk=pk)

    # Sample context data based on template type
    sample_contexts = {
        "claim_reported": {
            "claim_number": "SIN-2024-0001",
            "policy_number": "POL-2024-0001",
            "incident_date": "15/01/2024",
            "incident_location": "Oficina Central",
            "incident_description": "Daño por inundación",
            "estimated_loss": "1500.00",
            "reported_by": "Juan Pérez",
            "assigned_to": "María González",
        },
        "policy_expiring": {
            "user_name": "Juan Pérez",
            "policy_number": "POL-2024-0001",
            "insurance_company": "Seguros Pichincha",
            "end_date": "15/02/2024",
            "days_remaining": "7",
        },
        "payment_due": {
            "user_name": "Juan Pérez",
            "invoice_number": "INV-2024-0001",
            "policy_number": "POL-2024-0001",
            "due_date": "15/02/2024",
            "total_amount": "1250.00",
            "days_remaining": "7",
        },
        "policy_expired": {
            "policy_number": "POL-2024-0001",
            "company_name": "Seguros Pichincha",
            "expiry_date": "01/01/2024",
            "policy_url": "/policies/1/",
        },
        "invoice_overdue": {
            "invoice_number": "INV-2024-0001",
            "amount": "1250.00",
            "days_overdue": "5",
            "due_date": "15/01/2024",
            "invoice_url": "/invoices/1/",
        },
        "claim_overdue": {
            "claim_number": "SIN-2024-0001",
            "policy_number": "POL-2024-0001",
            "days_overdue": "12",
            "last_update": "10/01/2024 09:30",
            "claim_url": "/claims/1/",
        },
        "document_overdue": {
            "document_name": "Reporte policial",
            "claim_number": "SIN-2024-0001",
            "days_overdue": "8",
            "deadline": "05/01/2024",
            "claim_url": "/claims/1/",
        },
        "maintenance_required": {
            "asset_code": "ACT-2024-0001",
            "asset_name": "Laptop Dell",
            "condition": "Regular",
            "asset_url": "/assets/1/",
        },
        "system_alert": {
            "alert_name": "Alerta General",
            "message": "Mantenimiento programado del sistema a las 22:00.",
            "priority": "normal",
        },
        "settlement_signed": {
            "user_name": "Juan Pérez",
            "claim_number": "SIN-2024-0001",
            "settlement_number": "FIN-2024-0001",
            "final_amount": "980.00",
        },
        "payment_completed": {
            "user_name": "Juan Pérez",
            "claim_number": "SIN-2024-0001",
            "settlement_number": "FIN-2024-0001",
            "payment_amount": "980.00",
            "payment_date": "20/01/2024",
        },
    }

    context = sample_contexts.get(template.template_type, {})

    # Render template with sample data
    rendered_subject = template.render_subject(context)
    rendered_html = template.render_body_html(context)
    rendered_text = template.render_body_text(context)

    return render(
        request,
        "notifications/email_template_test.html",
        {
            "template": template,
            "context": context,
            "rendered_subject": rendered_subject,
            "rendered_html": rendered_html,
            "rendered_text": rendered_text,
            "title": _("Probar Plantilla de Email"),
        },
    )


# Notification Views
@login_required
def notification_list(request):
    """List user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Mark notifications as read if requested
    if request.method == "POST" and "mark_read" in request.POST:
        notification_ids = request.POST.getlist("notification_ids")
        Notification.objects.filter(user=request.user, id__in=notification_ids).update(
            is_read=True
        )
        messages.success(request, _("Notificaciones marcadas como leídas."))

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(
        request,
        "notifications/notification_list.html",
        {
            "page_obj": page_obj,
            "unread_count": unread_count,
        },
    )


@login_required
def notification_mark_read(request, pk):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    return redirect("notifications:notification_list")


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, _("Todas las notificaciones marcadas como leídas."))
    return redirect("notifications:notification_list")


# Alert Views
@login_required
@permission_required("notifications.alerts_read", raise_exception=True)
def alert_list(request):
    """List all alerts"""
    alerts = Alert.objects.all().order_by("-created_at")
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "notifications/alert_list.html",
        {
            "page_obj": page_obj,
        },
    )


@login_required
@permission_required("notifications.alerts_create", raise_exception=True)
def alert_create(request):
    """Create new alert"""
    if request.method == "POST":
        form = AlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.created_by = request.user
            alert.save()
            form.save_m2m()  # Save many-to-many relationships

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="create",
                entity_type="alert",
                entity_id=str(alert.id),
                description=f"Alerta creada: {alert.name}",
                new_values={
                    "name": alert.name,
                    "alert_type": alert.alert_type,
                    "frequency": alert.frequency,
                },
            )

            messages.success(request, _("Alerta creada exitosamente."))
            return redirect("notifications:alert_detail", pk=alert.pk)
    else:
        form = AlertForm()

    return render(
        request,
        "notifications/alert_form.html",
        {
            "form": form,
            "title": _("Crear Nueva Alerta"),
            "submit_text": _("Crear Alerta"),
        },
    )


@login_required
@permission_required("notifications.alerts_read", raise_exception=True)
def alert_detail(request, pk):
    """View alert details"""
    alert = get_object_or_404(Alert, pk=pk)

    # Check permissions - users can only see alerts they created or alerts they're recipients of
    if not request.user.has_role_permission("alerts_read"):
        if (
            alert.created_by != request.user
            and request.user not in alert.recipients.all()
        ):
            messages.error(request, _("No tienes permisos para ver esta alerta."))
            return redirect("notifications:alert_list")

    return render(
        request,
        "notifications/alert_detail.html",
        {
            "alert": alert,
        },
    )


@login_required
@permission_required("notifications.alerts_write", raise_exception=True)
def alert_edit(request, pk):
    """Edit existing alert"""
    alert = get_object_or_404(Alert, pk=pk)

    # Check ownership
    if (
        not request.user.has_role_permission("alerts_write")
        and alert.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para editar esta alerta."))
        return redirect("notifications:alert_detail", pk=pk)

    if request.method == "POST":
        form = AlertForm(request.POST, instance=alert)
        if form.is_valid():
            old_values = {
                "name": alert.name,
                "alert_type": alert.alert_type,
                "frequency": alert.frequency,
                "is_active": alert.is_active,
            }

            updated_alert = form.save()

            new_values = {
                "name": updated_alert.name,
                "alert_type": updated_alert.alert_type,
                "frequency": updated_alert.frequency,
                "is_active": updated_alert.is_active,
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="update",
                entity_type="alert",
                entity_id=str(updated_alert.id),
                description=f"Alerta actualizada: {updated_alert.name}",
                old_values=old_values,
                new_values=new_values,
            )

            messages.success(request, _("Alerta actualizada exitosamente."))
            return redirect("notifications:alert_detail", pk=updated_alert.pk)
    else:
        form = AlertForm(instance=alert)

    return render(
        request,
        "notifications/alert_form.html",
        {
            "form": form,
            "alert": alert,
            "title": _("Editar Alerta"),
            "submit_text": _("Actualizar Alerta"),
        },
    )


@login_required
@permission_required("notifications.alerts_execute", raise_exception=True)
def alert_execute(request, pk):
    """Execute an alert manually"""
    alert = get_object_or_404(Alert, pk=pk)

    # Check permissions
    if (
        not request.user.has_role_permission("alerts_execute")
        and alert.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para ejecutar esta alerta."))
        return redirect("notifications:alert_detail", pk=pk)

    results = alert.execute()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="execute",
        entity_type="alert",
        entity_id=str(alert.id),
        description=f'Alerta ejecutada manualmente: {alert.name} - {results.get("notifications_created", 0)} notificaciones, {results.get("emails_sent", 0)} emails',
    )

    messages.success(
        request,
        f'Alerta ejecutada: {results.get("notifications_created", 0)} notificaciones creadas, {results.get("emails_sent", 0)} emails enviados.',
    )

    return redirect("notifications:alert_detail", pk=pk)


@login_required
@permission_required("notifications.alerts_delete", raise_exception=True)
def alert_delete(request, pk):
    """Delete alert"""
    alert = get_object_or_404(Alert, pk=pk)

    # Check ownership
    if (
        not request.user.has_role_permission("alerts_delete")
        and alert.created_by != request.user
    ):
        messages.error(request, _("No tienes permisos para eliminar esta alerta."))
        return redirect("notifications:alert_detail", pk=pk)

    alert_name = alert.name
    alert.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="delete",
        entity_type="alert",
        entity_id=str(pk),
        description=f"Alerta eliminada: {alert_name}",
    )

    messages.success(request, _("Alerta eliminada exitosamente."))
    return redirect("notifications:alert_list")


@login_required
@permission_required("notifications.alerts_execute", raise_exception=True)
def run_all_alerts(request):
    """Run all scheduled alerts"""
    results = run_scheduled_alerts()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="execute",
        entity_type="alert",
        entity_id="0",
        description=f'Ejecución masiva de alertas: {results.get("alerts_executed", 0)} alertas, {results.get("notifications_created", 0)} notificaciones, {results.get("emails_sent", 0)} emails',
    )

    messages.success(
        request,
        f'Alertas ejecutadas: {results.get("alerts_executed", 0)} alertas procesadas, {results.get("notifications_created", 0)} notificaciones creadas, {results.get("emails_sent", 0)} emails enviados.',
    )

    return redirect("notifications:alert_list")
