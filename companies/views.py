from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from audit.models import AuditLog

from .forms import (
    EmissionRightsForm,
    InsuranceCompanyForm,
    InsuranceCompanySearchForm,
    PolicyRetentionForm,
    RetentionTypeForm,
)
from .models import EmissionRights, InsuranceCompany, PolicyRetention, RetentionType


# Insurance Companies Views
@login_required
def insurance_company_list(request):
    """List all insurance companies with search and filtering"""
    search_form = InsuranceCompanySearchForm(request.GET)
    companies = InsuranceCompany.objects.all().order_by("-created_at")

    if search_form.is_valid():
        search = search_form.cleaned_data.get("search")
        is_active = search_form.cleaned_data.get("is_active")

        if search:
            companies = companies.filter(
                Q(name__icontains=search)
                | Q(ruc__icontains=search)
                | Q(email__icontains=search)
                | Q(contact_person__icontains=search)
            )

        if is_active:
            if is_active == "active":
                companies = companies.filter(is_active=True)
            elif is_active == "inactive":
                companies = companies.filter(is_active=False)

    # Pagination
    paginator = Paginator(companies, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_companies = companies.count()
    active_companies = companies.filter(is_active=True).count()
    companies_with_policies = (
        companies.filter(policies__isnull=False).distinct().count()
    )

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_companies": total_companies,
        "active_companies": active_companies,
        "companies_with_policies": companies_with_policies,
    }

    return render(request, "companies/insurance_company_list.html", context)


@login_required
@permission_required("companies.insurance_companies_create", raise_exception=True)
def insurance_company_create(request):
    """Create new insurance company"""
    if request.method == "POST":
        form = InsuranceCompanyForm(request.POST)
        if form.is_valid():
            company = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="create",
                entity_type="insurance_company",
                entity_id=str(company.id),
                description=f"Compañía aseguradora creada: {company.name}",
                new_values={
                    "name": company.name,
                    "ruc": company.ruc,
                    "email": company.email,
                    "is_active": company.is_active,
                },
            )

            messages.success(request, _("Compañía aseguradora creada exitosamente."))
            return redirect("companies:insurance_company_detail", pk=company.pk)
    else:
        form = InsuranceCompanyForm()

    return render(
        request,
        "companies/insurance_company_form.html",
        {
            "form": form,
            "title": _("Crear Nueva Compañía Aseguradora"),
            "submit_text": _("Crear Compañía"),
        },
    )


@login_required
def insurance_company_detail(request, pk):
    """View insurance company details"""
    company = get_object_or_404(
        InsuranceCompany.objects.prefetch_related("policies"), pk=pk
    )

    # Get related data
    active_policies = company.policies.filter(status="active")
    total_policies = company.policies.count()
    total_insured_value = (
        active_policies.aggregate(total=Sum("insured_value"))["total"] or 0
    )

    # Recent policies
    recent_policies = company.policies.order_by("-created_at")[:5]

    context = {
        "company": company,
        "active_policies": active_policies.count(),
        "total_policies": total_policies,
        "total_insured_value": total_insured_value,
        "recent_policies": recent_policies,
    }

    return render(request, "companies/insurance_company_detail.html", context)


@login_required
@permission_required("companies.insurance_companies_write", raise_exception=True)
def insurance_company_edit(request, pk):
    """Edit insurance company"""
    company = get_object_or_404(InsuranceCompany, pk=pk)

    if request.method == "POST":
        form = InsuranceCompanyForm(request.POST, instance=company)
        if form.is_valid():
            old_values = {
                "name": company.name,
                "ruc": company.ruc,
                "email": company.email,
                "is_active": company.is_active,
            }

            updated_company = form.save()

            new_values = {
                "name": updated_company.name,
                "ruc": updated_company.ruc,
                "email": updated_company.email,
                "is_active": updated_company.is_active,
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type="update",
                entity_type="insurance_company",
                entity_id=str(updated_company.id),
                description=f"Compañía aseguradora actualizada: {updated_company.name}",
                old_values=old_values,
                new_values=new_values,
            )

            messages.success(
                request, _("Compañía aseguradora actualizada exitosamente.")
            )
            return redirect("companies:insurance_company_detail", pk=updated_company.pk)
    else:
        form = InsuranceCompanyForm(instance=company)

    return render(
        request,
        "companies/insurance_company_form.html",
        {
            "form": form,
            "company": company,
            "title": _("Editar Compañía Aseguradora"),
            "submit_text": _("Actualizar Compañía"),
        },
    )


@login_required
@permission_required("companies.insurance_companies_delete", raise_exception=True)
def insurance_company_delete(request, pk):
    """Delete insurance company"""
    company = get_object_or_404(InsuranceCompany, pk=pk)

    # Check if company has policies
    if company.policies.exists():
        messages.error(
            request,
            _("No se puede eliminar la compañía porque tiene pólizas asociadas."),
        )
        return redirect("companies:insurance_company_detail", pk=pk)

    company_name = company.name
    company.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="delete",
        entity_type="insurance_company",
        entity_id=str(pk),
        description=f"Compañía aseguradora eliminada: {company_name}",
    )

    messages.success(request, _("Compañía aseguradora eliminada exitosamente."))
    return redirect("companies:insurance_company_list")


@login_required
@permission_required("companies.insurance_companies_manage", raise_exception=True)
def insurance_company_toggle_active(request, pk):
    """Toggle insurance company active status"""
    company = get_object_or_404(InsuranceCompany, pk=pk)

    old_status = company.is_active
    company.is_active = not company.is_active
    company.save()

    action = "activada" if company.is_active else "desactivada"

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type="update",
        entity_type="insurance_company",
        entity_id=str(company.id),
        description=f"Compañía {action}: {company.name}",
        old_values={"is_active": old_status},
        new_values={"is_active": company.is_active},
    )

    messages.success(
        request, _("Compañía %(action)s exitosamente.") % {"action": action}
    )
    return redirect("companies:insurance_company_detail", pk=pk)


@login_required
def emission_rights_list(request):
    """List all emission rights configurations"""
    if not request.user.get_role_permissions().__contains__("insurance_companies_read"):
        messages.error(
            request, _("No tienes permisos para ver la configuración financiera.")
        )
        return redirect("accounts:dashboard")

    # Get filter parameters
    is_active = request.GET.get("is_active", "true")
    search = request.GET.get("search", "")

    # Base queryset
    queryset = EmissionRights.objects.all()

    # Apply filters
    if is_active == "true":
        queryset = queryset.filter(is_active=True)
    elif is_active == "false":
        queryset = queryset.filter(is_active=False)

    if search:
        queryset = queryset.filter(
            Q(min_amount__icontains=search)
            | Q(max_amount__icontains=search)
            | Q(emission_right__icontains=search)
        )

    emission_rights = queryset.order_by("-valid_from", "min_amount")

    context = {
        "emission_rights": emission_rights,
        "is_active_filter": is_active,
        "search": search,
        "title": _("Derechos de Emisión"),
    }

    return render(request, "companies/emission_rights_list.html", context)


@login_required
def emission_rights_create(request):
    """Create new emission rights configuration"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(
            request, _("No tienes permisos para crear configuración financiera.")
        )
        return redirect("companies:emission_rights_list")

    if request.method == "POST":
        form = EmissionRightsForm(request.POST)
        if form.is_valid():
            emission_right = form.save(commit=False)
            emission_right.created_by = request.user
            emission_right.save()
            messages.success(request, _("Derecho de emisión creado exitosamente."))
            return redirect("companies:emission_rights_list")
    else:
        form = EmissionRightsForm()

    return render(
        request,
        "companies/emission_rights_form.html",
        {
            "form": form,
            "title": _("Crear Derecho de Emisión"),
            "submit_text": _("Crear"),
        },
    )


@login_required
def emission_rights_edit(request, pk):
    """Edit emission rights configuration"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(
            request, _("No tienes permisos para editar configuración financiera.")
        )
        return redirect("companies:emission_rights_list")

    emission_right = get_object_or_404(EmissionRights, pk=pk)

    if request.method == "POST":
        form = EmissionRightsForm(request.POST, instance=emission_right)
        if form.is_valid():
            form.save()
            messages.success(request, _("Derecho de emisión actualizado exitosamente."))
            return redirect("companies:emission_rights_list")
    else:
        form = EmissionRightsForm(instance=emission_right)

    return render(
        request,
        "companies/emission_rights_form.html",
        {
            "form": form,
            "title": _("Editar Derecho de Emisión"),
            "submit_text": _("Actualizar"),
            "emission_right": emission_right,
        },
    )


@login_required
def emission_rights_delete(request, pk):
    """Delete emission rights configuration"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_delete"
    ):
        messages.error(
            request, _("No tienes permisos para eliminar configuración financiera.")
        )
        return redirect("companies:emission_rights_list")

    emission_right = get_object_or_404(EmissionRights, pk=pk)

    if request.method == "POST":
        emission_right.delete()
        messages.success(request, _("Derecho de emisión eliminado exitosamente."))
        return redirect("companies:emission_rights_list")

    return render(
        request,
        "companies/emission_rights_confirm_delete.html",
        {
            "emission_right": emission_right,
            "title": _("Eliminar Derecho de Emisión"),
        },
    )


@login_required
def retention_types_list(request):
    """List all retention types"""
    if not request.user.get_role_permissions().__contains__("insurance_companies_read"):
        messages.error(request, _("No tienes permisos para ver tipos de retención."))
        return redirect("accounts:dashboard")

    retention_types = RetentionType.objects.all().order_by("name")

    return render(
        request,
        "companies/retention_types_list.html",
        {
            "retention_types": retention_types,
            "title": _("Tipos de Retención"),
        },
    )


@login_required
def retention_types_create(request):
    """Create new retention type"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(request, _("No tienes permisos para crear tipos de retención."))
        return redirect("companies:retention_types_list")

    if request.method == "POST":
        form = RetentionTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tipo de retención creado exitosamente."))
            return redirect("companies:retention_types_list")
    else:
        form = RetentionTypeForm()

    return render(
        request,
        "companies/retention_types_form.html",
        {
            "form": form,
            "title": _("Crear Tipo de Retención"),
            "submit_text": _("Crear"),
        },
    )


@login_required
def retention_types_edit(request, pk):
    """Edit retention type"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(request, _("No tienes permisos para editar tipos de retención."))
        return redirect("companies:retention_types_list")

    retention_type = get_object_or_404(RetentionType, pk=pk)

    if request.method == "POST":
        form = RetentionTypeForm(request.POST, instance=retention_type)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tipo de retención actualizado exitosamente."))
            return redirect("companies:retention_types_list")
    else:
        form = RetentionTypeForm(instance=retention_type)

    return render(
        request,
        "companies/retention_types_form.html",
        {
            "form": form,
            "title": _("Editar Tipo de Retención"),
            "submit_text": _("Actualizar"),
            "retention_type": retention_type,
        },
    )


@login_required
def policy_retentions_list(request):
    """List all policy retentions"""
    if not request.user.get_role_permissions().__contains__("insurance_companies_read"):
        messages.error(request, _("No tienes permisos para ver retenciones de póliza."))
        return redirect("accounts:dashboard")

    policy_retentions = PolicyRetention.objects.select_related(
        "policy", "retention_type", "created_by"
    ).order_by("-created_at")

    return render(
        request,
        "companies/policy_retentions_list.html",
        {
            "policy_retentions": policy_retentions,
            "title": _("Retenciones de Póliza"),
        },
    )


@login_required
def policy_retentions_create(request):
    """Create new policy retention"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(
            request, _("No tienes permisos para crear retenciones de póliza.")
        )
        return redirect("companies:policy_retentions_list")

    if request.method == "POST":
        form = PolicyRetentionForm(request.POST)
        if form.is_valid():
            policy_retention = form.save(commit=False)
            policy_retention.created_by = request.user
            policy_retention.save()
            messages.success(request, _("Retención de póliza creada exitosamente."))
            return redirect("companies:policy_retentions_list")
    else:
        form = PolicyRetentionForm()

    return render(
        request,
        "companies/policy_retentions_form.html",
        {
            "form": form,
            "title": _("Crear Retención de Póliza"),
            "submit_text": _("Crear"),
        },
    )


@login_required
def policy_retentions_edit(request, pk):
    """Edit policy retention"""
    if not request.user.get_role_permissions().__contains__(
        "insurance_companies_write"
    ):
        messages.error(
            request, _("No tienes permisos para editar retenciones de póliza.")
        )
        return redirect("companies:policy_retentions_list")

    policy_retention = get_object_or_404(PolicyRetention, pk=pk)

    if request.method == "POST":
        form = PolicyRetentionForm(request.POST, instance=policy_retention)
        if form.is_valid():
            form.save()
            messages.success(
                request, _("Retención de póliza actualizada exitosamente.")
            )
            return redirect("companies:policy_retentions_list")
    else:
        form = PolicyRetentionForm(instance=policy_retention)

    return render(
        request,
        "companies/policy_retentions_form.html",
        {
            "form": form,
            "title": _("Editar Retención de Póliza"),
            "submit_text": _("Actualizar"),
            "policy_retention": policy_retention,
        },
    )
