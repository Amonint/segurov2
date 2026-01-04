from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from .models import Broker
from .forms import BrokerForm, BrokerSearchForm
from audit.models import AuditLog

@login_required
def broker_list(request):
    """List all brokers with search and filtering"""
    search_form = BrokerSearchForm(request.GET)
    brokers = Broker.objects.all().order_by('-created_at')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        is_active = search_form.cleaned_data.get('is_active')
        commission_range = search_form.cleaned_data.get('commission_range')

        if search:
            brokers = brokers.filter(
                Q(name__icontains=search) |
                Q(ruc__icontains=search) |
                Q(email__icontains=search) |
                Q(contact_person__icontains=search)
            )

        if is_active:
            if is_active == 'active':
                brokers = brokers.filter(is_active=True)
            elif is_active == 'inactive':
                brokers = brokers.filter(is_active=False)

        if commission_range:
            if commission_range == 'low':
                brokers = brokers.filter(commission_percentage__lt=5)
            elif commission_range == 'medium':
                brokers = brokers.filter(commission_percentage__gte=5, commission_percentage__lt=15)
            elif commission_range == 'high':
                brokers = brokers.filter(commission_percentage__gte=15)

    # Pagination
    paginator = Paginator(brokers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_brokers = brokers.count()
    active_brokers = brokers.filter(is_active=True).count()
    brokers_with_policies = brokers.filter(policies__isnull=False).distinct().count()

    # Commission statistics
    avg_commission = brokers.filter(is_active=True).aggregate(
        avg=models.Avg('commission_percentage')
    )['avg'] or 0

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_brokers': total_brokers,
        'active_brokers': active_brokers,
        'brokers_with_policies': brokers_with_policies,
        'avg_commission': round(avg_commission, 2),
    }

    return render(request, 'brokers/broker_list.html', context)


@login_required
def broker_detail(request, pk):
    """View broker details"""
    broker = get_object_or_404(
        Broker.objects.prefetch_related('policies'),
        pk=pk
    )

    # Get related data
    active_policies = broker.policies.filter(status='active')
    total_policies = broker.policies.count()
    total_insured_value = active_policies.aggregate(
        total=models.Sum('insured_value')
    )['total'] or 0

    # Commission calculations
    total_commission = 0
    if total_insured_value and broker.commission_percentage:
        total_commission = (total_insured_value * broker.commission_percentage) / 100

    # Recent policies
    recent_policies = broker.policies.order_by('-created_at')[:5]

    context = {
        'broker': broker,
        'active_policies': active_policies.count(),
        'total_policies': total_policies,
        'total_insured_value': total_insured_value,
        'total_commission': total_commission,
        'recent_policies': recent_policies,
    }

    return render(request, 'brokers/broker_detail.html', context)


@login_required
@permission_required('brokers.brokers_create', raise_exception=True)
def broker_create(request):
    """Create new broker"""
    if request.method == 'POST':
        form = BrokerForm(request.POST)
        if form.is_valid():
            broker = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='create',
                entity_type='broker',
                entity_id=str(broker.id),
                description=f'Corredor creado: {broker.name}',
                new_values={
                    'name': broker.name,
                    'ruc': broker.ruc,
                    'email': broker.email,
                    'commission_percentage': str(broker.commission_percentage),
                    'is_active': broker.is_active
                }
            )

            messages.success(request, _('Corredor creado exitosamente.'))
            return redirect('brokers:broker_detail', pk=broker.pk)
    else:
        form = BrokerForm()

    return render(request, 'brokers/broker_form.html', {
        'form': form,
        'title': _('Crear Nuevo Corredor'),
        'submit_text': _('Crear Corredor'),
    })


@login_required
@permission_required('brokers.brokers_write', raise_exception=True)
def broker_edit(request, pk):
    """Edit existing broker"""
    broker = get_object_or_404(Broker, pk=pk)

    if request.method == 'POST':
        form = BrokerForm(request.POST, instance=broker)
        if form.is_valid():
            old_values = {
                'name': broker.name,
                'ruc': broker.ruc,
                'email': broker.email,
                'commission_percentage': str(broker.commission_percentage),
                'is_active': broker.is_active
            }

            updated_broker = form.save()

            new_values = {
                'name': updated_broker.name,
                'ruc': updated_broker.ruc,
                'email': updated_broker.email,
                'commission_percentage': str(updated_broker.commission_percentage),
                'is_active': updated_broker.is_active
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='broker',
                entity_id=str(updated_broker.id),
                description=f'Corredor actualizado: {updated_broker.name}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Corredor actualizado exitosamente.'))
            return redirect('brokers:broker_detail', pk=updated_broker.pk)
    else:
        form = BrokerForm(instance=broker)

    return render(request, 'brokers/broker_form.html', {
        'form': form,
        'broker': broker,
        'title': _('Editar Corredor'),
        'submit_text': _('Actualizar Corredor'),
    })


@login_required
@permission_required('brokers.brokers_delete', raise_exception=True)
def broker_delete(request, pk):
    """Delete broker"""
    broker = get_object_or_404(Broker, pk=pk)

    # Check if broker has policies
    if broker.policies.exists():
        messages.error(request, _('No se puede eliminar el corredor porque tiene pólizas asociadas.'))
        return redirect('brokers:broker_detail', pk=pk)

    broker_name = broker.name
    broker.delete()

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='broker',
        entity_id=str(pk),
        description=f'Corredor eliminado: {broker_name}'
    )

    messages.success(request, _('Corredor eliminado exitosamente.'))
    return redirect('brokers:broker_list')


@login_required
@permission_required('brokers.brokers_manage', raise_exception=True)
def broker_toggle_active(request, pk):
    """Toggle broker active status"""
    broker = get_object_or_404(Broker, pk=pk)

    old_status = broker.is_active
    broker.is_active = not broker.is_active
    broker.save()

    action = 'activado' if broker.is_active else 'desactivado'

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='update',
        entity_type='broker',
        entity_id=str(broker.id),
        description=f'Corredor {action}: {broker.name}',
        old_values={'is_active': old_status},
        new_values={'is_active': broker.is_active}
    )

    messages.success(request, _('Corredor %(action)s exitosamente.') % {'action': action})
    return redirect('brokers:broker_detail', pk=pk)
