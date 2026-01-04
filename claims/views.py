from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Claim, ClaimDocument

@login_required
def claim_list(request):
    """List all claims"""
    claims = Claim.objects.all().select_related('policy', 'reported_by', 'assigned_to')
    return render(request, 'claims/claim_list.html', {'claims': claims})

@login_required
def claim_detail(request, pk):
    """View claim details"""
    claim = get_object_or_404(Claim, pk=pk)
    timeline = claim.timeline.all().order_by('-created_at')
    documents = claim.documents.all()
    return render(request, 'claims/claim_detail.html', {
        'claim': claim,
        'timeline': timeline,
        'documents': documents
    })

@login_required
def claim_create(request):
    """Create new claim"""
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('claims:claim_list')

@login_required
def claim_edit(request, pk):
    """Edit existing claim"""
    claim = get_object_or_404(Claim, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('claims:claim_detail', pk=pk)

@login_required
def claim_update_status(request, pk):
    """Update claim status"""
    claim = get_object_or_404(Claim, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('claims:claim_detail', pk=pk)

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
