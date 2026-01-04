from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Broker

@login_required
def broker_list(request):
    """List all brokers"""
    brokers = Broker.objects.all()
    return render(request, 'brokers/broker_list.html', {'brokers': brokers})

@login_required
def broker_detail(request, pk):
    """View broker details"""
    broker = get_object_or_404(Broker, pk=pk)
    return render(request, 'brokers/broker_detail.html', {'broker': broker})

@login_required
def broker_create(request):
    """Create new broker"""
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('brokers:broker_list')

@login_required
def broker_edit(request, pk):
    """Edit existing broker"""
    broker = get_object_or_404(Broker, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('brokers:broker_detail', pk=pk)

@login_required
def broker_delete(request, pk):
    """Delete broker"""
    broker = get_object_or_404(Broker, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('brokers:broker_list')
