from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Policy, PolicyDocument

@login_required
def policy_list(request):
    """List all policies"""
    policies = Policy.objects.all().select_related('insurance_company', 'broker', 'responsible_user')
    return render(request, 'policies/policy_list.html', {'policies': policies})

@login_required
def policy_detail(request, pk):
    """View policy details"""
    policy = get_object_or_404(Policy, pk=pk)
    return render(request, 'policies/policy_detail.html', {'policy': policy})

@login_required
def policy_create(request):
    """Create new policy"""
    # Placeholder - will be implemented with forms
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('policies:policy_list')

@login_required
def policy_edit(request, pk):
    """Edit existing policy"""
    policy = get_object_or_404(Policy, pk=pk)
    # Placeholder - will be implemented with forms
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('policies:policy_detail', pk=pk)

@login_required
def policy_delete(request, pk):
    """Delete policy"""
    policy = get_object_or_404(Policy, pk=pk)
    # Placeholder - will be implemented with forms
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('policies:policy_list')

@login_required
def policy_documents(request, pk):
    """View policy documents"""
    policy = get_object_or_404(Policy, pk=pk)
    documents = policy.documents.all()
    return render(request, 'policies/policy_documents.html', {
        'policy': policy,
        'documents': documents
    })

@login_required
def policy_document_upload(request, pk):
    """Upload policy document"""
    policy = get_object_or_404(Policy, pk=pk)
    # Placeholder - will be implemented with forms
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('policies:policy_documents', pk=pk)

@login_required
def policy_document_delete(request, pk):
    """Delete policy document"""
    document = get_object_or_404(PolicyDocument, pk=pk)
    policy_pk = document.policy.pk
    # Placeholder - will be implemented
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('policies:policy_documents', pk=policy_pk)
