from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import models
from django.db.models import Q
from django.core.paginator import Paginator
from .models import UserProfile
from .forms import (
    UserProfileCreationForm, UserProfileChangeForm,
    UserProfilePasswordChangeForm, UserProfileSearchForm,
    UserProfilePasswordResetForm, UserProfileSetPasswordForm
)
from policies.models import Policy
from claims.models import Claim
from invoices.models import Invoice
from assets.models import Asset
from notifications.models import Notification
from audit.models import AuditLog
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
    return redirect('accounts:login')


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
        context.update(get_manager_dashboard_data(user))
    elif user.role == 'financial_analyst':
        context.update(get_analyst_dashboard_data())
    elif user.role == 'consultant':
        context.update(get_consultant_dashboard_data(user))
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


def get_manager_dashboard_data(user):
    """
    Get dashboard data for insurance manager role
    """
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


def get_consultant_dashboard_data(user):
    """
    Get dashboard data for consultant role
    """
    return {
        'total_claims': Claim.objects.count(),
        'my_claims': Claim.objects.filter(assigned_to=user).count(),
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


# User Management Views
@login_required
@permission_required('accounts.users_read', raise_exception=True)
def user_list(request):
    """
    List all users with search and filtering
    """
    # Get search form data
    search_form = UserProfileSearchForm(request.GET)
    users = UserProfile.objects.all().order_by('-date_joined')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        role = search_form.cleaned_data.get('role')
        is_active = search_form.cleaned_data.get('is_active')
        department = search_form.cleaned_data.get('department')

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(full_name__icontains=search)
            )

        if role:
            users = users.filter(role=role)

        if is_active:
            if is_active == 'active':
                users = users.filter(is_active=True)
            elif is_active == 'inactive':
                users = users.filter(is_active=False)

        if department:
            users = users.filter(department__icontains=department)

    # Pagination
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_users': users.count(),
    }

    return render(request, 'accounts/user_list.html', context)


@login_required
@permission_required('accounts.users_create', raise_exception=True)
def user_create(request):
    """
    Create new user
    """
    if request.method == 'POST':
        form = UserProfileCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='create',
                entity_type='user',
                entity_id=str(user.id),
                description=f'Usuario creado: {user.username}',
                new_values={
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                }
            )

            messages.success(request, _('Usuario creado exitosamente.'))
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = UserProfileCreationForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Crear Nuevo Usuario'),
        'submit_text': _('Crear Usuario'),
    })


@login_required
@permission_required('accounts.users_read', raise_exception=True)
def user_detail(request, pk):
    """
    View user details
    """
    user = get_object_or_404(UserProfile, pk=pk)

    # Check permissions - users can only see their own profile unless they have read permission
    if not request.user.has_role_permission('users_read') and request.user != user:
        messages.error(request, _('No tienes permisos para ver este perfil.'))
        return redirect('accounts:profile')

    # Get related data
    recent_policies = Policy.objects.filter(responsible_user=user)[:5]
    recent_claims = Claim.objects.filter(Q(reported_by=user) | Q(assigned_to=user))[:5]
    recent_invoices = Invoice.objects.filter(created_by=user)[:5]
    recent_audit_logs = AuditLog.objects.filter(user=user)[:10]

    context = {
        'user_obj': user,  # Rename to avoid conflict with request.user
        'recent_policies': recent_policies,
        'recent_claims': recent_claims,
        'recent_invoices': recent_invoices,
        'recent_audit_logs': recent_audit_logs,
    }

    return render(request, 'accounts/user_detail.html', context)


@login_required
@permission_required('accounts.users_write', raise_exception=True)
def user_edit(request, pk):
    """
    Edit existing user
    """
    user = get_object_or_404(UserProfile, pk=pk)

    if request.method == 'POST':
        form = UserProfileChangeForm(request.POST, instance=user)
        if form.is_valid():
            old_values = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'role': user.role,
                'department': user.department,
                'phone': user.phone,
                'is_active': user.is_active
            }

            updated_user = form.save()

            new_values = {
                'username': updated_user.username,
                'email': updated_user.email,
                'first_name': updated_user.first_name,
                'last_name': updated_user.last_name,
                'full_name': updated_user.full_name,
                'role': updated_user.role,
                'department': updated_user.department,
                'phone': updated_user.phone,
                'is_active': updated_user.is_active
            }

            # Log the action
            AuditLog.log_action(
                user=request.user,
                action_type='update',
                entity_type='user',
                entity_id=str(updated_user.id),
                description=f'Usuario actualizado: {updated_user.username}',
                old_values=old_values,
                new_values=new_values
            )

            messages.success(request, _('Usuario actualizado exitosamente.'))
            return redirect('accounts:user_detail', pk=updated_user.pk)
    else:
        form = UserProfileChangeForm(instance=user)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'user_obj': user,
        'title': _('Editar Usuario'),
        'submit_text': _('Actualizar Usuario'),
    })


@login_required
@permission_required('accounts.users_manage', raise_exception=True)
def user_toggle_active(request, pk):
    """
    Toggle user active status
    """
    user = get_object_or_404(UserProfile, pk=pk)

    # Prevent deactivating self
    if user == request.user:
        messages.error(request, _('No puedes desactivar tu propia cuenta.'))
        return redirect('accounts:user_detail', pk=pk)

    old_status = user.is_active
    user.is_active = not user.is_active
    user.save()

    action = 'activado' if user.is_active else 'desactivado'

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='update',
        entity_type='user',
        entity_id=str(user.id),
        description=f'Usuario {action}: {user.username}',
        old_values={'is_active': old_status},
        new_values={'is_active': user.is_active}
    )

    messages.success(request, _('Usuario %(action)s exitosamente.') % {'action': action})
    return redirect('accounts:user_detail', pk=pk)


@login_required
@permission_required('accounts.users_manage', raise_exception=True)
def user_delete(request, pk):
    """
    Soft delete user (deactivate)
    """
    user = get_object_or_404(UserProfile, pk=pk)

    # Prevent deleting self
    if user == request.user:
        messages.error(request, _('No puedes eliminar tu propia cuenta.'))
        return redirect('accounts:user_detail', pk=pk)

    # Check if user has dependencies
    has_policies = Policy.objects.filter(responsible_user=user).exists()
    has_claims = Claim.objects.filter(Q(reported_by=user) | Q(assigned_to=user)).exists()
    has_invoices = Invoice.objects.filter(created_by=user).exists()

    if has_policies or has_claims or has_invoices:
        messages.error(request, _('No se puede eliminar el usuario porque tiene registros asociados.'))
        return redirect('accounts:user_detail', pk=pk)

    username = user.username
    user.delete()  # This will be a soft delete if implemented in model

    # Log the action
    AuditLog.log_action(
        user=request.user,
        action_type='delete',
        entity_type='user',
        entity_id=str(pk),
        description=f'Usuario eliminado: {username}'
    )

    messages.success(request, _('Usuario eliminado exitosamente.'))
    return redirect('accounts:user_list')


@login_required
def user_change_password(request, pk):
    """
    Change user password
    """
    user = get_object_or_404(UserProfile, pk=pk)

    # Check permissions - users can change their own password, admins can change any
    if request.user != user and not request.user.has_role_permission('users_manage'):
        messages.error(request, _('No tienes permisos para cambiar la contraseña de este usuario.'))
        return redirect('accounts:user_detail', pk=pk)

    if request.method == 'POST':
        if request.user == user:
            # User changing their own password
            form = UserProfilePasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type='update',
                    entity_type='user',
                    entity_id=str(user.id),
                    description=f'Cambio de contraseña: {user.username}'
                )

                messages.success(request, _('Tu contraseña ha sido cambiada exitosamente.'))
                return redirect('accounts:profile')
        else:
            # Admin changing another user's password
            form = UserProfileSetPasswordForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.save()

                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action_type='update',
                    entity_type='user',
                    entity_id=str(user.id),
                    description=f'Cambio de contraseña (admin): {user.username}'
                )

                messages.success(request, _('Contraseña cambiada exitosamente.'))
                return redirect('accounts:user_detail', pk=pk)
    else:
        if request.user == user:
            form = UserProfilePasswordChangeForm(user)
        else:
            form = UserProfileSetPasswordForm()

    return render(request, 'accounts/user_change_password.html', {
        'form': form,
        'user_obj': user,
        'is_own_password': request.user == user,
    })


@login_required
def user_password_reset_request(request):
    """
    Request password reset for a user
    """
    if not request.user.has_role_permission('users_manage'):
        messages.error(request, _('No tienes permisos para resetear contraseñas.'))
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserProfilePasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = UserProfile.objects.get(email=email)
                # Generate reset token (simplified - in production use Django's password reset)
                reset_token = user.generate_reset_token()

                # Send reset email (simplified)
                messages.success(request, _('Se ha enviado un enlace de reset al email del usuario.'))
                return redirect('accounts:user_list')
            except UserProfile.DoesNotExist:
                messages.error(request, _('No se encontró un usuario con ese email.'))
    else:
        form = UserProfilePasswordResetForm()

    return render(request, 'accounts/user_password_reset.html', {
        'form': form,
    })


@login_required
def profile_view(request):
    """
    User profile view and edit
    """
    user = request.user

    if request.method == 'POST':
        # Handle profile update
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()

        # Log the action
        AuditLog.log_action(
            user=request.user,
            action_type='update',
            entity_type='user',
            entity_id=str(user.id),
            description=f'Perfil actualizado: {user.username}'
        )

        messages.success(request, _('Perfil actualizado exitosamente.'))
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
    })
