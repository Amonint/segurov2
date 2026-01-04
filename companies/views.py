from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import InsuranceCompany, EmissionRights

@login_required
def company_list(request):
    """List all insurance companies"""
    companies = InsuranceCompany.objects.all()
    return render(request, 'companies/company_list.html', {'companies': companies})

@login_required
def company_detail(request, pk):
    """View company details"""
    company = get_object_or_404(InsuranceCompany, pk=pk)
    return render(request, 'companies/company_detail.html', {'company': company})

@login_required
def company_create(request):
    """Create new company"""
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('companies:company_list')

@login_required
def company_edit(request, pk):
    """Edit existing company"""
    company = get_object_or_404(InsuranceCompany, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('companies:company_detail', pk=pk)

@login_required
def company_delete(request, pk):
    """Delete company"""
    company = get_object_or_404(InsuranceCompany, pk=pk)
    messages.info(request, _('Funcionalidad en desarrollo'))
    return redirect('companies:company_list')
