from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from policies.models import Policy
from claims.models import Claim
from invoices.models import Invoice

@login_required
def report_list(request):
    """List available reports"""
    return render(request, 'reports/report_list.html')

@login_required
def policies_report(request):
    """Policies report"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    policies = Policy.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    # Aggregate data
    total_policies = policies.count()
    active_policies = policies.filter(status='active').count()
    expired_policies = policies.filter(status='expired').count()

    # Group by insurance company
    company_stats = policies.values('insurance_company__name').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'total_policies': total_policies,
        'active_policies': active_policies,
        'expired_policies': expired_policies,
        'company_stats': company_stats,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/policies_report.html', context)

@login_required
def claims_report(request):
    """Claims report"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    claims = Claim.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    # Aggregate data
    total_claims = claims.count()
    status_stats = claims.values('status').annotate(count=Count('id'))

    # Calculate total estimated loss
    total_estimated_loss = claims.aggregate(total=Sum('estimated_loss'))['total'] or 0

    context = {
        'total_claims': total_claims,
        'status_stats': status_stats,
        'total_estimated_loss': total_estimated_loss,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/claims_report.html', context)

@login_required
def invoices_report(request):
    """Invoices report"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    invoices = Invoice.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    # Aggregate data
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(payment_status='paid').count()
    pending_invoices = invoices.filter(payment_status='pending').count()
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
    paid_amount = invoices.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': total_amount - paid_amount,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/invoices_report.html', context)

@login_required
def financial_report(request):
    """Financial summary report"""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # Last 3 months

    # Revenue data
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    monthly_revenue = invoices.filter(payment_status='paid').extra(
        select={'month': "strftime('%%Y-%%m', created_at)"}
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    # Outstanding payments
    outstanding_invoices = Invoice.objects.filter(payment_status='pending')
    total_outstanding = outstanding_invoices.aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'monthly_revenue': monthly_revenue,
        'total_outstanding': total_outstanding,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'reports/financial_report.html', context)

@login_required
def export_policies_report(request):
    """Export policies report to Excel"""
    messages.info(request, _('Funcionalidad de exportación en desarrollo'))
    return redirect('reports:policies_report')

@login_required
def export_claims_report(request):
    """Export claims report to Excel"""
    messages.info(request, _('Funcionalidad de exportación en desarrollo'))
    return redirect('reports:claims_report')

@login_required
def export_financial_report(request):
    """Export financial report to Excel"""
    messages.info(request, _('Funcionalidad de exportación en desarrollo'))
    return redirect('reports:financial_report')
