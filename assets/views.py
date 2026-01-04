from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from .models import Asset
from .forms import AssetForm, AssetSearchForm, AssetCustodianChangeForm
from audit.models import AuditLog

@login_required
def asset_list(request):
    """List all assets with search and filtering"""
    search_form = AssetSearchForm(request.GET)
    assets = Asset.objects.all().select_related(
        'custodian', 'responsible_user', 'insurance_policy'
    ).order_by('-created_at')

    # Filter based on user role
    if request.user.role == 'requester':
        # Requesters can only see their own assets
        assets = assets.filter(custodian=request.user)
    # Other roles can see all assets based on permissions

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        asset_type = search_form.cleaned_data.get('asset_type')
        condition_status = search_form.cleaned_data.get('condition_status')
        is_insured = search_form.cleaned_data.get('is_insured')
        custodian = search_form.cleaned_data.get('custodian')

        if search:
            assets = assets.filter(
                Q(asset_code__icontains=search) |
                Q(name__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(location__icontains=search)
            )

        if asset_type:
            assets = assets.filter(asset_type=asset_type)

        if condition_status:
            assets = assets.filter(condition_status=condition_status)

        if is_insured:
            if is_insured == 'insured':
                assets = assets.filter(is_insured=True)
            elif is_insured == 'uninsured':
                assets = assets.filter(is_insured=False)

        if custodian:
            assets = assets.filter(custodian=custodian)

    # Pagination
    paginator = Paginator(assets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_assets = assets.count()
    insured_assets = assets.filter(is_insured=True).count()
    total_value = assets.aggregate(
        total=Sum('current_value')
    )['total'] or 0

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_assets': total_assets,
        'insured_assets': insured_assets,
        'total_value': total_value,
    }

    return render(request, 'assets/asset_list.html', context)


@login_required
def asset_detail(request, pk):
    """View asset details"""
    asset = get_object_or_404(
        Asset.objects.select_related(
            'custodian', 'responsible_user', 'insurance_policy__insurance_company'
        ),
        pk=pk
    )

    # Check permissions - requesters can only see their own assets
    if request.user.role == 'requester' and asset.custodian != request.user:
        messages.error(request, _('No tienes permisos para ver este activo.'))
        return redirect('assets:asset_list')

    # Calculate depreciation
    depreciation_years = (timezone.now().date() - asset.acquisition_date).days / 365.25
    depreciated_value = asset.calculate_depreciation(depreciation_years)

    context = {
        'asset': asset,
        'depreciation_years': round(depreciation_years, 1),
        'depreciated_value': depreciated_value,
        'has_valid_insurance': asset.has_valid_insurance(),
    }

    return render(request, 'assets/asset_detail.html', context)


@login_required
@permission_required('assets.assets_create', raise_exception=True)
def asset_create(request):
    """Create new asset"""
    if request.method == 'POST':
        form = AssetForm(request.POST, user=request.user)
        if form.is_valid():
            asset = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='create',
                entity_type='asset',
                entity_id=str(asset.id),
                description=f'Activo creado: {asset.asset_code} - {asset.name}',
                new_values={
                    'asset_code': asset.asset_code,
                    'name': asset.name,
                    'asset_type': asset.asset_type,
                    'acquisition_cost': str(asset.acquisition_cost),
                    'is_insured': asset.is_insured
                }
            )

            messages.success(request, _('Activo creado exitosamente.'))
            return redirect('assets:asset_detail', pk=asset.pk)
    else:
        form = AssetForm(user=request.user)

    return render(request, 'assets/asset_form.html', {
        'form': form,
        'title': _('Crear Nuevo Activo'),
        'submit_text': _('Crear Activo'),
    })


@login_required
@permission_required('assets.assets_write', raise_exception=True)
def asset_edit(request, pk):
    """Edit existing asset"""
    asset = get_object_or_404(Asset, pk=pk)

    # Check permissions - requesters can only edit their own assets
    if request.user.role == 'requester' and asset.custodian != request.user:
        messages.error(request, _('No tienes permisos para editar este activo.'))
        return redirect('assets:asset_detail', pk=pk)

    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset, user=request.user)
        if form.is_valid():
            old_values = {
                'asset_code': asset.asset_code,
                'name': asset.name,
                'asset_type': asset.asset_type,
                'acquisition_cost': str(asset.acquisition_cost),
                'current_value': str(asset.current_value),
                'condition_status': asset.condition_status,
                'is_insured': asset.is_insured,
                'custodian': asset.custodian.username if asset.custodian else None
            }

            updated_asset = form.save()

            new_values = {
                'asset_code': updated_asset.asset_code,
                'name': updated_asset.name,
                'asset_type': updated_asset.asset_type,
                'acquisition_cost': str(updated_asset.acquisition_cost),
                'current_value': str(updated_asset.current_value),
                'condition_status': updated_asset.condition_status,
                'is_insured': updated_asset.is_insured,
                'custodian': updated_asset.custodian.username if updated_asset.custodian else None
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='asset',
                entity_id=str(updated_asset.id),
                description=f'Activo actualizado: {updated_asset.asset_code} - {updated_asset.name}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Activo actualizado exitosamente.'))
            return redirect('assets:asset_detail', pk=updated_asset.pk)
    else:
        form = AssetForm(instance=asset, user=request.user)

    return render(request, 'assets/asset_form.html', {
        'form': form,
        'asset': asset,
        'title': _('Editar Activo'),
        'submit_text': _('Actualizar Activo'),
    })


@login_required
@permission_required('assets.assets_write', raise_exception=True)
def asset_change_custodian(request, pk):
    """Change asset custodian"""
    asset = get_object_or_404(Asset, pk=pk)

    # Check permissions - requesters can only change custodian of their own assets
    if request.user.role == 'requester' and asset.custodian != request.user:
        messages.error(request, _('No tienes permisos para cambiar el custodio de este activo.'))
        return redirect('assets:asset_detail', pk=pk)

    if request.method == 'POST':
        form = AssetCustodianChangeForm(request.POST, instance=asset)
        if form.is_valid():
            old_custodian = asset.custodian.username if asset.custodian else None
            updated_asset = form.save()

            new_custodian = updated_asset.custodian.username if updated_asset.custodian else None

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='asset',
                entity_id=str(updated_asset.id),
                description=f'Custodio cambiado: {updated_asset.asset_code} - {old_custodian} → {new_custodian}',
                old_values={'custodian': old_custodian},
                new_values={'custodian': new_custodian}
            )

            messages.success(request, _('Custodio del activo actualizado exitosamente.'))
            return redirect('assets:asset_detail', pk=updated_asset.pk)
    else:
        form = AssetCustodianChangeForm(instance=asset)

    return render(request, 'assets/asset_change_custodian.html', {
        'form': form,
        'asset': asset,
    })


@login_required
@permission_required('assets.assets_delete', raise_exception=True)
def asset_delete(request, pk):
    """Delete asset"""
    asset = get_object_or_404(Asset, pk=pk)

    # Check permissions - requesters can only delete their own assets
    if request.user.role == 'requester' and asset.custodian != request.user:
        messages.error(request, _('No tienes permisos para eliminar este activo.'))
        return redirect('assets:asset_detail', pk=pk)

    # Check if asset has claims
    if hasattr(asset, 'claims') and asset.claims.exists():
        messages.error(request, _('No se puede eliminar el activo porque tiene siniestros asociados.'))
        return redirect('assets:asset_detail', pk=pk)

    asset_code = asset.asset_code
    asset_name = asset.name
    asset.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='asset',
        entity_id=str(pk),
        description=f'Activo eliminado: {asset_code} - {asset_name}'
    )

    messages.success(request, _('Activo eliminado exitosamente.'))
    return redirect('assets:asset_list')


@login_required
@permission_required('assets.assets_write', raise_exception=True)
def asset_update_value(request, pk):
    """Update asset current value based on depreciation"""
    asset = get_object_or_404(Asset, pk=pk)

    # Check permissions - requesters can only update their own assets
    if request.user.role == 'requester' and asset.custodian != request.user:
        messages.error(request, _('No tienes permisos para actualizar este activo.'))
        return redirect('assets:asset_detail', pk=pk)

    old_value = asset.current_value
    asset.update_current_value()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='update',
        entity_type='asset',
        entity_id=str(asset.id),
        description=f'Valor actualizado por depreciación: {asset.asset_code}',
        old_values={'current_value': str(old_value)},
        new_values={'current_value': str(asset.current_value)}
    )

    messages.success(request, _('Valor del activo actualizado según depreciación.'))
    return redirect('assets:asset_detail', pk=pk)
