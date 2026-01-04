from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import models
from .models import UserProfile
from policies.models import Policy
from claims.models import Claim
from invoices.models import Invoice
from assets.models import Asset
from notifications.models import Notification
import datetime


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Custom login view
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                next_url = request.GET.get('next') or reverse('accounts:dashboard')
                messages.success(request, _('Bienvenido, %(name)s!') % {'name': user.get_full_name()})
                return redirect(next_url)
            else:
                messages.error(request, _('Credenciales inválidas. Por favor, inténtelo de nuevo.'))
        else:
            messages.error(request, _('Por favor, ingrese usuario y contraseña.'))

    return render(request, 'accounts/login_simple.html')


@login_required
def logout_view(request):
    """
    Custom logout view
    """
    logout(request)
    messages.info(request, _('Ha cerrado sesión exitosamente.'))
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main dashboard view with role-based content
    """
    user = request.user
    context = {
        'user': user,
        'user_permissions': user.get_role_permissions(),
    }

    # Role-based dashboard data
    if user.role == 'admin':
        context.update(get_admin_dashboard_data())
    elif user.role == 'insurance_manager':
        context.update(get_manager_dashboard_data())
    elif user.role == 'financial_analyst':
        context.update(get_analyst_dashboard_data())
    elif user.role == 'consultant':
        context.update(get_consultant_dashboard_data())
    elif user.role == 'requester':
        context.update(get_requester_dashboard_data(user))

    return render(request, 'accounts/dashboard.html', context)


def get_admin_dashboard_data():
    """
    Get dashboard data for admin role
    """
    today = datetime.date.today()

    return {
        'total_policies': Policy.objects.count(),
        'active_policies': Policy.objects.filter(status='active').count(),
        'expiring_policies_30': Policy.objects.filter(
            end_date__lte=today + datetime.timedelta(days=30),
            end_date__gte=today,
            status='active'
        ).count(),
        'expiring_policies_7': Policy.objects.filter(
            end_date__lte=today + datetime.timedelta(days=7),
            end_date__gte=today,
            status='active'
        ).count(),
        'pending_invoices': Invoice.objects.filter(payment_status='pending').count(),
        'overdue_invoices': Invoice.objects.filter(
            payment_status='pending',
            due_date__lt=today
        ).count(),
        'early_payment_invoices': Invoice.objects.filter(
            payment_status='pending',
            due_date__lte=today + datetime.timedelta(days=20),
            due_date__gte=today
        ).count(),
        'total_pending_amount': Invoice.objects.filter(
            payment_status='pending'
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0,
        'claims_by_status': Claim.objects.values('status').annotate(count=models.Count('id')),
        'overdue_claims': Claim.objects.filter(
            status__in=['documentation_pending', 'sent_to_insurer', 'under_evaluation'],
            created_at__lte=timezone.now() - datetime.timedelta(days=8)
        ).count(),
    }


def get_manager_dashboard_data():
    """
    Get dashboard data for insurance manager role
    """
    user = request.user
    today = datetime.date.today()

    return {
        'my_policies': Policy.objects.filter(responsible_user=user).count(),
        'active_policies': Policy.objects.filter(status='active').count(),
        'expiring_policies_30': Policy.objects.filter(
            end_date__lte=today + datetime.timedelta(days=30),
            end_date__gte=today,
            status='active'
        ).count(),
        'total_claims': Claim.objects.count(),
        'pending_claims': Claim.objects.filter(status__in=['reported', 'documentation_pending']).count(),
        'claims_under_evaluation': Claim.objects.filter(status='under_evaluation').count(),
    }


def get_analyst_dashboard_data():
    """
    Get dashboard data for financial analyst role
    """
    today = datetime.date.today()

    return {
        'total_invoices': Invoice.objects.count(),
        'paid_invoices': Invoice.objects.filter(payment_status='paid').count(),
        'pending_invoices': Invoice.objects.filter(payment_status='pending').count(),
        'overdue_invoices': Invoice.objects.filter(
            payment_status='pending',
            due_date__lt=today
        ).count(),
        'total_revenue': Invoice.objects.filter(
            payment_status='paid'
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0,
    }


def get_consultant_dashboard_data():
    """
    Get dashboard data for consultant role
    """
    return {
        'total_claims': Claim.objects.count(),
        'my_claims': Claim.objects.filter(assigned_to=request.user).count(),
        'pending_claims': Claim.objects.filter(status__in=['reported', 'documentation_pending']).count(),
    }


def get_requester_dashboard_data(user):
    """
    Get dashboard data for requester (custodian) role
    """
    return {
        'my_assets': Asset.objects.filter(custodian=user).count(),
        'insured_assets': Asset.objects.filter(custodian=user, is_insured=True).count(),
        'my_claims': Claim.objects.filter(reported_by=user).count(),
        'pending_claims': Claim.objects.filter(
            reported_by=user,
            status__in=['reported', 'documentation_pending', 'sent_to_insurer', 'under_evaluation']
        ).count(),
    }


@login_required
def profile_view(request):
    """
    User profile view
    """
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        messages.success(request, _('Perfil actualizado exitosamente.'))
        return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'user': request.user,
    })
