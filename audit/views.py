from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .models import AuditLog


@login_required
@user_passes_test(lambda u: u.role in ["admin", "insurance_manager"])
def audit_log_list(request):
    """List audit logs with filtering"""
    # Get filter parameters
    action_type = request.GET.get("action_type", "")
    entity_type = request.GET.get("entity_type", "")
    user_filter = request.GET.get("user", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    # Build queryset
    logs = AuditLog.objects.all().select_related("user").order_by("-created_at")

    if action_type:
        logs = logs.filter(action_type=action_type)
    if entity_type:
        logs = logs.filter(entity_type=entity_type)
    if user_filter:
        logs = logs.filter(
            Q(user__username__icontains=user_filter)
            | Q(user__full_name__icontains=user_filter)
        )
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 50)  # 50 logs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options for dropdowns
    action_types = AuditLog.objects.values_list("action_type", flat=True).distinct()
    entity_types = AuditLog.objects.values_list("entity_type", flat=True).distinct()

    context = {
        "page_obj": page_obj,
        "action_types": action_types,
        "entity_types": entity_types,
        "filters": {
            "action_type": action_type,
            "entity_type": entity_type,
            "user": user_filter,
            "date_from": date_from,
            "date_to": date_to,
        },
    }

    return render(request, "audit/audit_log_list.html", context)


@login_required
@user_passes_test(lambda u: u.role in ["admin", "insurance_manager"])
def audit_log_detail(request, pk):
    """View detailed audit log entry"""
    log_entry = get_object_or_404(AuditLog, pk=pk)
    return render(request, "audit/audit_log_detail.html", {"log_entry": log_entry})


@login_required
@user_passes_test(lambda u: u.role == "admin")
def export_audit_logs(request):
    """Export audit logs to Excel/CSV"""
    messages.info(request, _("Funcionalidad de exportación en desarrollo"))
    return redirect("audit:audit_log_list")
