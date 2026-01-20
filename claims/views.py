from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Claim, ClaimDocument, ClaimSettlement, ClaimTimeline
from .forms import (
    ClaimEditForm, ClaimStatusChangeForm,
    ClaimSearchForm, ClaimSettlementForm
)
# Note: ClaimCreateForm removed - claims now created via AssetClaimReportForm
from audit.models import AuditLog
from accounts.decorators import permission_required as role_permission_required, requester_own_data_only


@login_required
def claim_list(request):
    """List all claims with search and filtering"""
    search_form = ClaimSearchForm(request.GET)
    claims = Claim.objects.all().select_related(
        'policy__insurance_company', 'reported_by', 'assigned_to'
    ).order_by('-created_at')

    # Filter based on user role - get base queryset for the user
    base_claims = claims  # Keep original for some stats
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

    # Statistics - Role-specific
    total_claims = claims.count()
    open_claims = claims.filter(
        status__in=['reportado', 'docs_pendientes', 'enviado_aseguradora', 'en_revision']
    ).count()
    closed_claims = claims.filter(status__in=['cerrado', 'pagado']).count()
    rejected_claims = claims.filter(status='rechazado').count()
    
    # SLA Alerts - Check for claims exceeding deadlines
    claims_with_alerts = []
    for claim in claims.filter(status__in=['docs_pendientes', 'enviado_aseguradora']):
        alerts = []
        if claim.verificar_sla_documentos():
            alerts.append('Documentación excede 8 días')
        if claim.verificar_sla_respuesta_aseguradora():
            alerts.append('Respuesta aseguradora excede 8 días hábiles')
        if claim.verificar_limite_maximo_30_dias():
            alerts.append('Límite máximo de 30 días excedido')
        
        if alerts:
            claims_with_alerts.append({
                'claim': claim,
                'alerts': alerts
            })
    
    # Additional statistics based on role
    if request.user.role == 'requester':
        # For requesters: show their personal stats
        needs_attention = claims.filter(
            status__in=['docs_pendientes', 'rechazado']
        ).count()
        resolved_claims = claims.filter(status__in=['cerrado', 'pagado']).count()
        
        context = {
            'page_obj': page_obj,
            'search_form': search_form,
            'total_claims': total_claims,
            'open_claims': open_claims,
            'closed_claims': closed_claims,
            'rejected_claims': rejected_claims,
            'needs_attention': needs_attention,
            'resolved_claims': resolved_claims,
            'claims_with_alerts': claims_with_alerts,
            'user_role': request.user.role,
        }
    elif request.user.role in ['insurance_manager', 'admin']:
        # For managers: show system-wide stats and assigned stats
        assigned_to_me = base_claims.filter(assigned_to=request.user).count()
        pending_review = base_claims.filter(
            status__in=['reportado', 'docs_pendientes']
        ).count()
        in_process = base_claims.filter(
            status__in=['enviado_aseguradora', 'en_revision', 'liquidado']
        ).count()
        
        context = {
            'page_obj': page_obj,
            'search_form': search_form,
            'total_claims': total_claims,
            'open_claims': open_claims,
            'closed_claims': closed_claims,
            'rejected_claims': rejected_claims,
            'assigned_to_me': assigned_to_me,
            'pending_review': pending_review,
            'in_process': in_process,
            'claims_with_alerts': claims_with_alerts,
            'user_role': request.user.role,
        }
    else:
        # For consultants and others: basic stats
        context = {
            'page_obj': page_obj,
            'search_form': search_form,
            'total_claims': total_claims,
            'open_claims': open_claims,
            'closed_claims': closed_claims,
            'rejected_claims': rejected_claims,
            'claims_with_alerts': claims_with_alerts,
            'user_role': request.user.role,
        }

    return render(request, 'claims/claim_list.html', context)


@login_required
@role_permission_required('claims_read')
def my_claims(request):
    """View for requesters to see their own claims with traceability"""
    # Get claims reported by the current user
    claims = Claim.objects.filter(
        reported_by=request.user
    ).select_related(
        'policy__insurance_company', 'asset', 'assigned_to'
    ).prefetch_related(
        'timeline', 'documents'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(claims, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_claims = claims.count()
    open_claims = claims.filter(
        status__in=['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation']
    ).count()
    resolved_claims = claims.filter(status__in=['closed', 'paid']).count()
    rejected_claims = claims.filter(status='rejected').count()
    
    # Claims needing attention (documentation pending or rejected)
    needs_attention = claims.filter(
        status__in=['documentation_pending', 'rejected']
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_claims': total_claims,
        'open_claims': open_claims,
        'resolved_claims': resolved_claims,
        'rejected_claims': rejected_claims,
        'needs_attention': needs_attention,
    }
    
    return render(request, 'claims/my_claims.html', context)



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
    settlement = claim.settlements.first() if hasattr(claim, 'settlements') and claim.settlements.exists() else None

    # Check if claim has overdue documents
    overdue_documents = []
    for doc in documents:
        if doc.is_overdue():
            overdue_documents.append(doc)

    # Calculate validation checklist for managers
    validation_checklist = []
    if request.user.has_role_permission('claims_update'):
        required_types = ['initial_report', 'photos', 'police_report', 'invoice']
        uploaded_types = [doc.document_type for doc in documents]
        
        for doc_type in required_types:
            is_present = doc_type in uploaded_types
            # get display name from model choices
            display_name = dict(ClaimDocument.DOCUMENT_TYPE_CHOICES).get(doc_type, doc_type)
            
            validation_checklist.append({
                'type': doc_type,
                'name': display_name,
                'is_present': is_present,
                'status_icon': 'bi-check-circle-fill text-green-500' if is_present else 'bi-x-circle-fill text-red-500',
                'status_text': _('Cargado') if is_present else _('Pendiente')
            })

    # Get latest status change note for feedback
    latest_status_note = ''
    if claim.status in ['documentation_pending', 'rejected']:
        last_change = claim.timeline.filter(event_type='status_change').order_by('-created_at').first()
        if last_change and last_change.notes:
            latest_status_note = last_change.notes
            
    context = {
        'claim': claim,
        'timeline': timeline,
        'documents': documents,
        'settlement': settlement,
        'overdue_documents': overdue_documents,
        'validation_checklist': validation_checklist,
        'can_edit': request.user.has_role_permission('claims_write') or claim.reported_by == request.user,
        'can_change_status': request.user.has_role_permission('claims_update'),
        'latest_status_note': latest_status_note,
    }

    return render(request, 'claims/claim_detail.html', context)

@login_required
@role_permission_required('claims_create')
def claim_create(request):
    """
    Redirect to assets list for claim reporting
    Claims are now reported from asset detail pages
    """
    messages.info(request, _('Para reportar un siniestro, seleccione el bien afectado de su lista de bienes'))
    return redirect('assets:asset_list')



@login_required
@role_permission_required('claims_write')
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
@role_permission_required('claims_write')
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
                    description=f'Estado de siniestro cambiado: {claim.claim_number} ({old_status} → {new_status})',
                    old_values={'status': old_status},
                    new_values={'status': new_status, 'notes': notes}
                )

                messages.success(request, _('Estado del siniestro actualizado exitosamente.'))
                
                # TDR Workflow: If status is 'liquidated', redirect to settlement creation
                if new_status == 'liquidated' and not hasattr(claim, 'settlement'):
                    return redirect('claims:claim_settlement_create', pk=claim.pk)
                    
                return redirect('claims:claim_detail', pk=claim.pk)

            except ValueError as e:
                messages.error(request, str(e))
    else:
        # Check for pre-selected status in GET parameters
        initial_status = request.GET.get('new_status') or request.GET.get('initial')
        
        initial_data = {}
        if initial_status:
            initial_data['new_status'] = initial_status
            
        form = ClaimStatusChangeForm(claim=claim, user=request.user, initial=initial_data)

    return render(request, 'claims/claim_change_status.html', {
        'form': form,
        'claim': claim,
    })


@login_required
@role_permission_required('claims_delete')
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
    if claim.documents.exists() or (hasattr(claim, 'settlements') and claim.settlements.exists()):
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
    
    # Check permissions - requesters can only see their own claims
    if request.user.role == 'requester' and claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para ver este siniestro.'))
        return redirect('claims:my_claims')
    
    documents = claim.documents.filter(status='active').order_by('-uploaded_at')
    return render(request, 'claims/claim_documents.html', {
        'claim': claim,
        'documents': documents
    })

@login_required
def claim_document_upload(request, pk):
    """Upload claim document"""
    claim = get_object_or_404(Claim, pk=pk)
    
    # Check permissions - requesters can only upload to their own claims
    if request.user.role == 'requester' and claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para subir documentos a este siniestro.'))
        return redirect('claims:my_claims')
    
    if request.method == 'POST':
        # Get form data
        document_name = request.POST.get('document_name')
        document_type = request.POST.get('document_type')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')
        
        if not document_name or not document_type or not file:
            messages.error(request, _('Por favor complete todos los campos requeridos.'))
            return redirect('claims:claim_documents', pk=pk)
        
        try:
            # Create document
            document = ClaimDocument.objects.create(
                claim=claim,
                document_name=document_name,
                document_type=document_type,
                description=description,
                file=file,
                uploaded_by=request.user,
                status='active'
            )
            
            messages.success(request, _('Documento subido exitosamente.'))
            return redirect('claims:claim_documents', pk=pk)
        except Exception as e:
            messages.error(request, _('Error al subir el documento: %(error)s') % {'error': str(e)})
            return redirect('claims:claim_documents', pk=pk)
    
    return render(request, 'claims/claim_document_upload.html', {
        'claim': claim,
        'document_types': ClaimDocument.DOCUMENT_TYPE_CHOICES
    })

@login_required
def claim_document_delete(request, pk):
    """Delete claim document"""
    document = get_object_or_404(ClaimDocument, pk=pk)
    claim_pk = document.claim.pk
    
    # Check permissions - requesters can only delete from their own claims
    if request.user.role == 'requester' and document.claim.reported_by != request.user:
        messages.error(request, _('No tienes permisos para eliminar este documento.'))
        return redirect('claims:my_claims')
    
    # Check if user has permission to delete documents
    if not request.user.has_role_permission('claims_write'):
        messages.error(request, _('No tienes permisos para eliminar documentos.'))
        return redirect('claims:claim_documents', pk=claim_pk)
    
    if request.method == 'POST':
        document_name = document.document_name
        # Soft delete - mark as deleted instead of actually deleting
        document.status = 'deleted'
        document.save()
        
        messages.success(request, _('Documento "%(name)s" eliminado exitosamente.') % {'name': document_name})
        return redirect('claims:claim_documents', pk=claim_pk)
    
    return render(request, 'claims/claim_document_delete_confirm.html', {
        'document': document,
        'claim': document.claim
    })


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
    if hasattr(claim, 'settlement'):
        messages.warning(request, _('Este siniestro ya tiene un finiquito creado.'))
        return redirect('claims:claim_settlement_detail', pk=claim.settlement.pk)

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
