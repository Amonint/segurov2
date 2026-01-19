from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Claim, ClaimDocument, ClaimSettlement, ClaimTimeline
from .forms import (
    ClaimCreateForm, ClaimEditForm, ClaimStatusChangeForm,
    ClaimSearchForm, ClaimSettlementForm
)
from audit.models import AuditLog

@login_required
def claim_list(request):
    """List all claims with search and filtering"""
    search_form = ClaimSearchForm(request.GET)
    claims = Claim.objects.all().select_related(
        'policy__insurance_company', 'reported_by', 'assigned_to'
    ).order_by('-created_at')

    # Filter based on user role
    if request.user.role == 'requester':
        # Requesters can only see their own claims
        claims = claims.filter(reported_by=request.user)

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        policy = search_form.cleaned_data.get('policy')
        reported_by = search_form.cleaned_data.get('reported_by')
        assigned_to = search_form.cleaned_data.get('assigned_to')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        overdue = search_form.cleaned_data.get('overdue')

        if search:
            claims = claims.filter(
                Q(claim_number__icontains=search) |
                Q(incident_description__icontains=search) |
                Q(policy__policy_number__icontains=search) |
                Q(asset_description__icontains=search)
            )

        if status:
            claims = claims.filter(status=status)

        if policy:
            claims = claims.filter(policy=policy)

        if reported_by:
            claims = claims.filter(reported_by=reported_by)

        if assigned_to:
            claims = claims.filter(assigned_to=assigned_to)

        if date_from:
            claims = claims.filter(incident_date__gte=date_from)

        if date_to:
            claims = claims.filter(incident_date__lte=date_to)

        if overdue:
            # Claims that are open but haven't been updated in more than 30 days
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            claims = claims.filter(
                status__in=['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation'],
                updated_at__lt=thirty_days_ago
            )

    # Pagination
    paginator = Paginator(claims, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_claims = claims.count()
    open_claims = claims.filter(
        status__in=['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation']
    ).count()
    closed_claims = claims.filter(status__in=['closed', 'paid', 'rejected']).count()

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_claims': total_claims,
        'open_claims': open_claims,
        'closed_claims': closed_claims,
    }

    return render(request, 'claims/claim_list.html', context)


@login_required
def claim_detail(request, pk):
    """View claim details"""
    claim = get_object_or_404(
        Claim.objects.select_related(
            'policy__insurance_company', 'reported_by', 'assigned_to'
        ),
        pk=pk
    )

    # Check permissions - requesters can only see their own claims
    if request.user.role == 'requester' and claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para ver este siniestro.'))
        return redirect('claims:claim_list')

    timeline = claim.timeline.all().order_by('-created_at')
    documents = claim.documents.all().order_by('-uploaded_at')

    # Get settlement if exists
    try:
        settlement = claim.settlement
    except ClaimSettlement.DoesNotExist:
        settlement = None

    # Check if claim has overdue documents
    overdue_documents = []
    for doc in documents:
        if doc.is_overdue():
            overdue_documents.append(doc)

    context = {
        'claim': claim,
        'timeline': timeline,
        'documents': documents,
        'settlement': settlement,
        'overdue_documents': overdue_documents,
        'can_edit': request.user.has_role_permission('claims_write') or claim.reported_by == request.user,
        'can_change_status': request.user.has_role_permission('claims_write'),
    }

    return render(request, 'claims/claim_detail.html', context)

@login_required
def claim_create(request):
    """Create new claim"""
    if 'claims_create' not in request.user.get_role_permissions():
        messages.error(request, _('No tienes permisos para crear siniestros.'))
        return redirect('claims:claim_list')

    if request.method == 'POST':
        form = ClaimCreateForm(request.POST, user=request.user)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.save()

            messages.success(request, _('Siniestro creado exitosamente.'))
            return redirect('claims:claim_detail', pk=claim.pk)
    else:
        form = ClaimCreateForm(user=request.user)

    return render(request, 'claims/claim_form.html', {
        'form': form,
        'title': _('Crear Nuevo Siniestro'),
        'submit_text': _('Crear Siniestro'),
    })

@login_required
@permission_required('claims.claims_write', raise_exception=True)
def claim_edit(request, pk):
    """Edit existing claim"""
    claim = get_object_or_404(Claim, pk=pk)

    # Check permissions - requesters can only edit their own claims
    if request.user.role == 'requester' and claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para editar este siniestro.'))
        return redirect('claims:claim_detail', pk=pk)

    # Only allow editing if claim is in early stages
    if claim.status in ['paid', 'closed', 'rejected']:
        messages.error(request, _('No se pueden editar siniestros que ya han sido finalizados.'))
        return redirect('claims:claim_detail', pk=pk)

    if request.method == 'POST':
        form = ClaimEditForm(request.POST, instance=claim, user=request.user)
        if form.is_valid():
            old_values = {
                'policy': claim.policy.policy_number if claim.policy else None,
                'incident_date': str(claim.incident_date),
                'report_date': str(claim.report_date),
                'incident_description': claim.incident_description,
                'estimated_loss': str(claim.estimated_loss),
                'assigned_to': claim.assigned_to.username if claim.assigned_to else None
            }

            updated_claim = form.save()

            new_values = {
                'policy': updated_claim.policy.policy_number if updated_claim.policy else None,
                'incident_date': str(updated_claim.incident_date),
                'report_date': str(updated_claim.report_date),
                'incident_description': updated_claim.incident_description,
                'estimated_loss': str(updated_claim.estimated_loss),
                'assigned_to': updated_claim.assigned_to.username if updated_claim.assigned_to else None
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='claim',
                entity_id=str(updated_claim.id),
                description=f'Siniestro actualizado: {updated_claim.claim_number}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Siniestro actualizado exitosamente.'))
            return redirect('claims:claim_detail', pk=updated_claim.pk)
    else:
        form = ClaimEditForm(instance=claim, user=request.user)

    return render(request, 'claims/claim_form.html', {
        'form': form,
        'claim': claim,
        'title': _('Editar Siniestro'),
        'submit_text': _('Actualizar Siniestro'),
    })


@login_required
@permission_required('claims.claims_write', raise_exception=True)
def claim_update_status(request, pk):
    """Update claim status"""
    claim = get_object_or_404(Claim, pk=pk)

    if request.method == 'POST':
        form = ClaimStatusChangeForm(request.POST, claim=claim, user=request.user)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            notes = form.cleaned_data.get('notes', '')

            old_status = claim.status
            try:
                claim.change_status(new_status, request.user, notes)

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type='update',
                    entity_type='claim',
                    entity_id=str(claim.id),
                    description=f'Estado de siniestro cambiado: {claim.claim_number} ({old_status} -> {new_status})',
                    old_values={'status': old_status},
                    new_values={'status': new_status, 'notes': notes}
                )

                messages.success(request, _('Estado del siniestro actualizado exitosamente.'))
                return redirect('claims:claim_detail', pk=claim.pk)

            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = ClaimStatusChangeForm(claim=claim, user=request.user)

    return render(request, 'claims/claim_change_status.html', {
        'form': form,
        'claim': claim,
    })


@login_required
@permission_required('claims.claims_delete', raise_exception=True)
def claim_delete(request, pk):
    """Delete claim"""
    claim = get_object_or_404(Claim, pk=pk)

    # Check permissions - requesters can only delete their own claims
    if request.user.role == 'requester' and claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para eliminar este siniestro.'))
        return redirect('claims:claim_detail', pk=pk)

    # Only allow deletion if claim is in early stages
    if claim.status not in ['reported', 'documentation_pending']:
        messages.error(request, _('Solo se pueden eliminar siniestros en estado inicial.'))
        return redirect('claims:claim_detail', pk=pk)

    # Check if claim has documents or settlements
    if claim.documents.exists() or ClaimSettlement.objects.filter(claim=claim).exists():
        messages.error(request, _('No se puede eliminar el siniestro porque tiene documentos o finiquitos asociados.'))
        return redirect('claims:claim_detail', pk=pk)

    claim_number = claim.claim_number
    claim.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='claim',
        entity_id=str(pk),
        description=f'Siniestro eliminado: {claim_number}'
    )

    messages.success(request, _('Siniestro eliminado exitosamente.'))
    return redirect('claims:claim_list')

@login_required
def claim_documents(request, pk):
    """View claim documents"""
    claim = get_object_or_404(Claim, pk=pk)
    documents = claim.documents.all()
    return render(request, 'claims/claim_documents.html', {
        'claim': claim,
        'documents': documents
    })

@login_required
def claim_document_upload(request, pk):
    """Upload claim document"""
    claim = get_object_or_404(Claim, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('claims:claim_documents', pk=pk)

@login_required
def claim_document_delete(request, pk):
    """Delete claim document"""
    document = get_object_or_404(ClaimDocument, pk=pk)
    claim_pk = document.claim.pk
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('claims:claim_documents', pk=claim_pk)


@login_required
def claim_settlements_list(request):
    """List all claim settlements"""
    if not request.user.get_role_permissions().__contains__('claims_read'):
        messages.error(request, _('No tienes permisos para ver finiquitos.'))
        return redirect('accounts:dashboard')

    settlements = ClaimSettlement.objects.select_related(
        'claim', 'claim__policy', 'created_by', 'approved_by'
    ).order_by('-created_at')

    return render(request, 'claims/claim_settlements_list.html', {
        'settlements': settlements,
        'title': _('Finiquitos de Siniestros'),
    })


@login_required
def claim_settlement_create(request, claim_pk):
    """Create settlement for a claim"""
    claim = get_object_or_404(Claim, pk=claim_pk)

    # Check permissions
    if not request.user.get_role_permissions().__contains__('claims_write'):
        messages.error(request, _('No tienes permisos para crear finiquitos.'))
        return redirect('claims:claim_detail', pk=claim_pk)

    # Check if settlement already exists
    existing_settlement = ClaimSettlement.objects.filter(claim=claim).first()
    if existing_settlement:
        messages.warning(request, _('Este siniestro ya tiene un finiquito creado.'))
        return redirect('claims:claim_settlement_detail', pk=existing_settlement.pk)

    if request.method == 'POST':
        form = ClaimSettlementForm(request.POST, request.FILES)
        if form.is_valid():
            settlement = form.save(commit=False)
            settlement.claim = claim
            settlement.created_by = request.user
            settlement.save()
            messages.success(request, _('Finiquito creado exitosamente.'))
            return redirect('claims:claim_settlement_detail', pk=settlement.pk)
    else:
        # Pre-populate with claim data
        initial_data = {
            'total_claim_amount': claim.estimated_loss or 0,
            'claim_reference_number': f"REF-{claim.claim_number}",
        }
        form = ClaimSettlementForm(initial=initial_data)

    return render(request, 'claims/claim_settlement_form.html', {
        'form': form,
        'claim': claim,
        'title': _('Crear Finiquito'),
        'submit_text': _('Crear Finiquito'),
    })


@login_required
def claim_settlement_detail(request, pk):
    """View settlement details"""
    settlement = get_object_or_404(
        ClaimSettlement.objects.select_related(
            'claim', 'claim__policy', 'created_by', 'approved_by'
        ),
        pk=pk
    )

    if not request.user.get_role_permissions().__contains__('claims_read'):
        messages.error(request, _('No tienes permisos para ver finiquitos.'))
        return redirect('accounts:dashboard')

    return render(request, 'claims/claim_settlement_detail.html', {
        'settlement': settlement,
        'title': _('Detalle del Finiquito'),
    })


@login_required
def claim_settlement_edit(request, pk):
    """Edit settlement"""
    settlement = get_object_or_404(ClaimSettlement, pk=pk)

    if not request.user.get_role_permissions().__contains__('claims_write'):
        messages.error(request, _('No tienes permisos para editar finiquitos.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    if request.method == 'POST':
        form = ClaimSettlementForm(request.POST, request.FILES, instance=settlement)
        if form.is_valid():
            form.save()
            messages.success(request, _('Finiquito actualizado exitosamente.'))
            return redirect('claims:claim_settlement_detail', pk=pk)
    else:
        form = ClaimSettlementForm(instance=settlement)

    return render(request, 'claims/claim_settlement_form.html', {
        'form': form,
        'settlement': settlement,
        'claim': settlement.claim,
        'title': _('Editar Finiquito'),
        'submit_text': _('Actualizar'),
    })


@login_required
def claim_settlement_approve(request, pk):
    """Approve settlement"""
    settlement = get_object_or_404(ClaimSettlement, pk=pk)

    if not request.user.get_role_permissions().__contains__('claims_write'):
        messages.error(request, _('No tienes permisos para aprobar finiquitos.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    if settlement.status != 'pending_approval':
        messages.error(request, _('El finiquito debe estar en estado "Pendiente de Aprobación".'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    settlement.status = 'approved'
    settlement.approved_by = request.user
    settlement.save()

    messages.success(request, _('Finiquito aprobado exitosamente.'))
    return redirect('claims:claim_settlement_detail', pk=pk)


@login_required
def claim_settlement_sign(request, pk):
    """Mark settlement as signed"""
    settlement = get_object_or_404(ClaimSettlement, pk=pk)

    if not request.user.get_role_permissions().__contains__('claims_write'):
        messages.error(request, _('No tienes permisos para firmar finiquitos.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    if settlement.status != 'approved':
        messages.error(request, _('El finiquito debe estar aprobado antes de firmarse.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    settlement.mark_as_signed()
    messages.success(request, _('Finiquito marcado como firmado.'))
    return redirect('claims:claim_settlement_detail', pk=pk)


@login_required
def claim_settlement_pay(request, pk):
    """Mark settlement as paid"""
    settlement = get_object_or_404(ClaimSettlement, pk=pk)

    if not request.user.get_role_permissions().__contains__('claims_write'):
        messages.error(request, _('No tienes permisos para marcar finiquitos como pagados.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    if settlement.status != 'signed':
        messages.error(request, _('El finiquito debe estar firmado antes de marcarlo como pagado.'))
        return redirect('claims:claim_settlement_detail', pk=pk)

    payment_reference = request.POST.get('payment_reference', '')

    settlement.mark_as_paid(payment_reference)
    messages.success(request, _('Finiquito marcado como pagado.'))
    return redirect('claims:claim_settlement_detail', pk=pk)
