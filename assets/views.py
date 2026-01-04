from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Asset

@login_required
def asset_list(request):
    """List all assets"""
    # Filter assets based on user role
    if request.user.role == 'requester':
        assets = Asset.objects.filter(custodian=request.user)
    else:
        assets = Asset.objects.all().select_related('custodian', 'responsible_user', 'insurance_policy')

    return render(request, 'assets/asset_list.html', {'assets': assets})

@login_required
def asset_detail(request, pk):
    """View asset details"""
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'assets/asset_detail.html', {'asset': asset})

@login_required
def asset_create(request):
    """Create new asset"""
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('assets:asset_list')

@login_required
def asset_edit(request, pk):
    """Edit existing asset"""
    asset = get_object_or_404(Asset, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('assets:asset_detail', pk=pk)

@login_required
def asset_delete(request, pk):
    """Delete asset"""
    asset = get_object_or_404(Asset, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('assets:asset_list')
