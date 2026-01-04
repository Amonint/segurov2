from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Invoice

@login_required
def invoice_list(request):
    """List all invoices"""
    invoices = Invoice.objects.all().select_related('policy', 'created_by')
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})

@login_required
def invoice_create(request):
    """Create new invoice"""
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('invoices:invoice_list')

@login_required
def invoice_edit(request, pk):
    """Edit existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('invoices:invoice_detail', pk=pk)

@login_required
def invoice_pdf(request, pk):
    """Generate invoice PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('invoices:invoice_detail', pk=pk)
