from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import Policy, PolicyDocument
from .forms import PolicyForm, PolicySearchForm, PolicyRenewalForm, PolicyDocumentForm, PolicyDocumentEditForm
from audit.models import AuditLog

@login_required
def policy_list(request):
    """List all policies with search and filtering"""
    # Get search form data
    search_form = PolicySearchForm(request.GET)
    policies = Policy.objects.all().select_related(
        'insurance_company', 'broker', 'responsible_user'
    ).order_by('-created_at')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        group_type = search_form.cleaned_data.get('group_type')
        insurance_company = search_form.cleaned_data.get('insurance_company')
        broker = search_form.cleaned_data.get('broker')
        responsible_user = search_form.cleaned_data.get('responsible_user')
        expiring_soon = search_form.cleaned_data.get('expiring_soon')

        if search:
            policies = policies.filter(
                Q(policy_number__icontains=search) |
                Q(insurance_company__name__icontains=search) |
                Q(broker__name__icontains=search) |
                Q(subgroup__icontains=search) |
                Q(branch__icontains=search)
            )

        if status:
            policies = policies.filter(status=status)

        if group_type:
            policies = policies.filter(group_type=group_type)

        if insurance_company:
            policies = policies.filter(insurance_company=insurance_company)

        if broker:
            policies = policies.filter(broker=broker)

        if responsible_user:
            policies = policies.filter(responsible_user=responsible_user)

        if expiring_soon:
            from datetime import timedelta
            from django.utils import timezone
            expiry_date = timezone.now().date() + timedelta(days=30)
            policies = policies.filter(
                end_date__lte=expiry_date,
                end_date__gte=timezone.now().date(),
                status='active'
            )

    # Pagination
    paginator = Paginator(policies, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_policies': policies.count(),
    }

    return render(request, 'policies/policy_list.html', context)


@login_required
def policy_detail(request, pk):
    """View policy details"""
    policy = get_object_or_404(
        Policy.objects.select_related(
            'insurance_company', 'broker', 'responsible_user'
        ),
        pk=pk
    )
    documents = policy.documents.all().order_by('-uploaded_at')

    # Check if policy is expiring soon
    is_expiring_soon = policy.is_expiring_soon(30)

    context = {
        'policy': policy,
        'documents': documents,
        'is_expiring_soon': is_expiring_soon,
    }

    return render(request, 'policies/policy_detail.html', context)


@login_required
@permission_required('policies.policies_create', raise_exception=True)
def policy_create(request):
    """Create new policy"""
    if request.method == 'POST':
        form = PolicyForm(request.POST)
        if form.is_valid():
            policy = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='create',
                entity_type='policy',
                entity_id=str(policy.id),
                description=f'Póliza creada: {policy.policy_number}',
                new_values={
                    'policy_number': policy.policy_number,
                    'insurance_company': policy.insurance_company.name,
                    'insured_value': str(policy.insured_value),
                    'status': policy.status
                }
            )

            messages.success(request, _('Póliza creada exitosamente.'))
            return redirect('policies:policy_detail', pk=policy.pk)
    else:
        form = PolicyForm()

    return render(request, 'policies/policy_form.html', {
        'form': form,
        'title': _('Crear Nueva Póliza'),
        'submit_text': _('Crear Póliza'),
    })


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_edit(request, pk):
    """Edit existing policy"""
    policy = get_object_or_404(Policy, pk=pk)

    if request.method == 'POST':
        form = PolicyForm(request.POST, instance=policy)
        if form.is_valid():
            old_values = {
                'policy_number': policy.policy_number,
                'insurance_company': policy.insurance_company.name if policy.insurance_company else None,
                'broker': policy.broker.name if policy.broker else None,
                'group_type': policy.group_type,
                'subgroup': policy.subgroup,
                'branch': policy.branch,
                'start_date': str(policy.start_date),
                'end_date': str(policy.end_date),
                'insured_value': str(policy.insured_value),
                'status': policy.status,
                'responsible_user': policy.responsible_user.username if policy.responsible_user else None
            }

            updated_policy = form.save()

            new_values = {
                'policy_number': updated_policy.policy_number,
                'insurance_company': updated_policy.insurance_company.name if updated_policy.insurance_company else None,
                'broker': updated_policy.broker.name if updated_policy.broker else None,
                'group_type': updated_policy.group_type,
                'subgroup': updated_policy.subgroup,
                'branch': updated_policy.branch,
                'start_date': str(updated_policy.start_date),
                'end_date': str(updated_policy.end_date),
                'insured_value': str(updated_policy.insured_value),
                'status': updated_policy.status,
                'responsible_user': updated_policy.responsible_user.username if updated_policy.responsible_user else None
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='policy',
                entity_id=str(updated_policy.id),
                description=f'Póliza actualizada: {updated_policy.policy_number}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Póliza actualizada exitosamente.'))
            return redirect('policies:policy_detail', pk=updated_policy.pk)
    else:
        form = PolicyForm(instance=policy)

    return render(request, 'policies/policy_form.html', {
        'form': form,
        'policy': policy,
        'title': _('Editar Póliza'),
        'submit_text': _('Actualizar Póliza'),
    })


@login_required
@permission_required('policies.policies_delete', raise_exception=True)
def policy_delete(request, pk):
    """Soft delete policy"""
    policy = get_object_or_404(Policy, pk=pk)

    # Check if policy has dependencies
    has_claims = policy.claims.exists()
    has_invoices = policy.invoices.exists()
    has_assets = policy.insured_assets.exists()

    if has_claims or has_invoices or has_assets:
        messages.error(request, _('No se puede eliminar la póliza porque tiene registros asociados (siniestros, facturas o bienes asegurados).'))
        return redirect('policies:policy_detail', pk=pk)

    policy_number = policy.policy_number
    policy.delete()  # This should be a soft delete in a real implementation

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='policy',
        entity_id=str(pk),
        description=f'Póliza eliminada: {policy_number}'
    )

    messages.success(request, _('Póliza eliminada exitosamente.'))
    return redirect('policies:policy_list')


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_renew(request, pk):
    """Renew policy"""
    policy = get_object_or_404(Policy, pk=pk)

    if request.method == 'POST':
        form = PolicyRenewalForm(request.POST, current_policy=policy)
        if form.is_valid():
            new_end_date = form.cleaned_data['new_end_date']
            observations = form.cleaned_data.get('observations', '')

            try:
                renewed_policy = policy.renew_policy(new_end_date)
                if observations:
                    renewed_policy.observations = observations
                    renewed_policy.save()

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type='update',
                    entity_type='policy',
                    entity_id=str(renewed_policy.id),
                    description=f'Póliza renovada: {policy.policy_number} -> {renewed_policy.policy_number}',
                    old_values={'status': 'active'},
                    new_values={'status': 'renewed', 'new_policy_number': renewed_policy.policy_number}
                )

                messages.success(request, _('Póliza renovada exitosamente.'))
                return redirect('policies:policy_detail', pk=renewed_policy.pk)
            except Exception as e:
                messages.error(request, f'Error al renovar la póliza: {str(e)}')
    else:
        form = PolicyRenewalForm(current_policy=policy)

    return render(request, 'policies/policy_renew.html', {
        'form': form,
        'policy': policy,
    })

@login_required
def policy_documents(request, pk):
    """View policy documents"""
    policy = get_object_or_404(Policy, pk=pk)
    documents = policy.documents.all().order_by('-uploaded_at')
    return render(request, 'policies/policy_documents.html', {
        'policy': policy,
        'documents': documents
    })


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_document_upload(request, pk):
    """Upload policy document"""
    policy = get_object_or_404(Policy, pk=pk)

    if request.method == 'POST':
        form = PolicyDocumentForm(request.POST, request.FILES, policy=policy, uploaded_by=request.user)
        if form.is_valid():
            document = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='document_upload',
                entity_type='policy',
                entity_id=str(policy.id),
                description=f'Documento subido a póliza {policy.policy_number}: {document.document_name}',
                new_values={
                    'document_name': document.document_name,
                    'document_type': document.document_type,
                    'file_size': document.file_size
                }
            )

            messages.success(request, _('Documento subido exitosamente.'))
            return redirect('policies:policy_documents', pk=policy.pk)
    else:
        form = PolicyDocumentForm(policy=policy, uploaded_by=request.user)

    # Get available document types for this policy
    available_types = PolicyDocument.get_document_types_for_policy(policy)

    return render(request, 'policies/policy_document_form.html', {
        'form': form,
        'policy': policy,
        'available_types': available_types,
        'title': _('Subir Documento'),
        'submit_text': _('Subir Documento'),
    })


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_document_edit(request, document_pk):
    """Edit policy document metadata"""
    document = get_object_or_404(PolicyDocument, pk=document_pk)
    policy = document.policy

    if request.method == 'POST':
        form = PolicyDocumentEditForm(request.POST, instance=document)
        if form.is_valid():
            old_values = {
                'document_name': document.document_name,
                'document_type': document.document_type,
                'description': document.description,
                'tags': document.tags
            }

            updated_document = form.save()

            new_values = {
                'document_name': updated_document.document_name,
                'document_type': updated_document.document_type,
                'description': updated_document.description,
                'tags': updated_document.tags
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='policy',
                entity_id=str(policy.id),
                description=f'Documento actualizado: {updated_document.document_name}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Documento actualizado exitosamente.'))
            return redirect('policies:policy_documents', pk=policy.pk)
    else:
        form = PolicyDocumentEditForm(instance=document)

    # Get available document types for this policy
    available_types = PolicyDocument.get_document_types_for_policy(policy)

    return render(request, 'policies/policy_document_form.html', {
        'form': form,
        'policy': policy,
        'document': document,
        'available_types': available_types,
        'title': _('Editar Documento'),
        'submit_text': _('Actualizar Documento'),
    })


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_document_new_version(request, document_pk):
    """Upload new version of a document"""
    document = get_object_or_404(PolicyDocument.objects.filter(is_latest_version=True), pk=document_pk)
    policy = document.policy

    if request.method == 'POST':
        form = PolicyDocumentForm(request.POST, request.FILES, policy=policy, uploaded_by=request.user)
        if form.is_valid():
            # Create new version
            new_version = document.create_new_version(
                new_file=form.cleaned_data['file'],
                uploaded_by=request.user,
                description=form.cleaned_data.get('description', '')
            )

            # Update metadata if provided
            new_version.document_name = form.cleaned_data.get('document_name', document.document_name)
            new_version.document_type = form.cleaned_data.get('document_type', document.document_type)
            new_version.tags = form.cleaned_data.get('tags', document.tags)
            new_version.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='document_upload',
                entity_type='policy',
                entity_id=str(policy.id),
                description=f'Nueva versión subida: {new_version.document_name} v{new_version.version}',
                new_values={
                    'document_name': new_version.document_name,
                    'version': new_version.version,
                    'file_size': new_version.file_size
                }
            )

            messages.success(request, _('Nueva versión del documento subida exitosamente.'))
            return redirect('policies:policy_document_versions', document_pk=document.pk)
    else:
        # Pre-fill form with current document data
        initial_data = {
            'document_name': document.document_name,
            'document_type': document.document_type,
            'description': document.description,
            'tags': document.tags,
        }
        form = PolicyDocumentForm(policy=policy, uploaded_by=request.user, initial=initial_data)

    return render(request, 'policies/policy_document_form.html', {
        'form': form,
        'policy': policy,
        'document': document,
        'is_new_version': True,
        'title': _('Subir Nueva Versión'),
        'submit_text': _('Subir Nueva Versión'),
    })


@login_required
def policy_document_versions(request, document_pk):
    """View all versions of a document"""
    document = get_object_or_404(PolicyDocument, pk=document_pk)
    policy = document.policy

    # Check permissions
    if not request.user.has_role_permission('policies_read'):
        if request.user != policy.responsible_user:
            messages.error(request, _('No tienes permisos para ver estos documentos.'))
            return redirect('policies:policy_detail', pk=policy.pk)

    versions = document.get_versions()

    return render(request, 'policies/policy_document_versions.html', {
        'policy': policy,
        'document': document,
        'versions': versions,
    })


@login_required
def policy_document_view(request, document_pk):
    """View document inline in browser"""
    document = get_object_or_404(PolicyDocument, pk=document_pk)
    policy = document.policy

    # Check permissions
    if not request.user.has_role_permission('policies_read'):
        if request.user != policy.responsible_user:
            messages.error(request, _('No tienes permisos para ver este documento.'))
            return redirect('policies:policy_detail', pk=policy.pk)

    if not document.can_view_inline():
        # Redirect to download instead
        return redirect('policies:policy_document_download', document_pk=document.pk)

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='export',
        entity_type='policy',
        entity_id=str(policy.id),
        description=f'Documento visualizado: {document.document_name}'
    )

    return render(request, 'policies/policy_document_view.html', {
        'policy': policy,
        'document': document,
    })


@login_required
@permission_required('policies.policies_write', raise_exception=True)
def policy_document_delete(request, document_pk):
    """Delete policy document"""
    document = get_object_or_404(PolicyDocument, pk=document_pk)
    policy = document.policy

    document_name = document.document_name
    document.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='policy',
        entity_id=str(policy.id),
        description=f'Documento eliminado de póliza {policy.policy_number}: {document_name}'
    )

    messages.success(request, _('Documento eliminado exitosamente.'))
    return redirect('policies:policy_documents', pk=policy.pk)


@login_required
def policy_document_download(request, document_pk):
    """Download policy document"""
    document = get_object_or_404(PolicyDocument, pk=document_pk)

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='export',
        entity_type='policy',
        entity_id=str(document.policy.id),
        description=f'Documento descargado: {document.document_name}'
    )

    # Return file
    response = HttpResponse(document.file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.document_name}"'
    return response


@require_POST
@login_required
def policy_bulk_action(request):
    """Handle bulk actions on policies"""
    action = request.POST.get('action')
    policy_ids = request.POST.getlist('policy_ids')

    if not policy_ids:
        messages.error(request, _('No se seleccionaron pólizas.'))
        return redirect('policies:policy_list')

    policies = Policy.objects.filter(id__in=policy_ids)

    if action == 'delete':
        if not request.user.has_perm('policies.policies_delete'):
            messages.error(request, _('No tienes permisos para eliminar pólizas.'))
            return redirect('policies:policy_list')

        deleted_count = 0
        for policy in policies:
            # Check if policy has dependencies
            if not (policy.claims.exists() or policy.invoices.exists() or policy.insured_assets.exists()):
                policy.delete()
                deleted_count += 1

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type='delete',
                    entity_type='policy',
                    entity_id=str(policy.id),
                    description=f'Póliza eliminada (bulk): {policy.policy_number}'
                )

        if deleted_count > 0:
            messages.success(request, f'{deleted_count} pólizas eliminadas exitosamente.')
        else:
            messages.warning(request, _('No se pudieron eliminar las pólizas seleccionadas porque tienen registros asociados.'))

    elif action == 'export':
        # Placeholder for export functionality
        messages.info(request, _('Funcionalidad de exportación en desarrollo.'))

    return redirect('policies:policy_list')
