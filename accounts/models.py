from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class UserProfile(AbstractUser):
    """
    Extended user model for the insurance management system.
    Includes role-based permissions and additional profile fields.
    """

    # Role choices - SIMPLIFIED TO 3 ROLES
    ROLE_CHOICES = [
        ('admin', _('Administrador')),
        ('insurance_manager', _('Gerente de Seguros')),
        ('requester', _('Custodio de Bienes')),
    ]

    # Additional fields
    full_name = models.CharField(
        _('Nombre completo'),
        max_length=255,
        blank=True
    )
    role = models.CharField(
        _('Rol'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='requester'
    )
    department = models.CharField(
        _('Departamento'),
        max_length=100,
        blank=True
    )
    phone = models.CharField(
        _('Teléfono'),
        max_length=20,
        blank=True
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Perfil de Usuario')
        verbose_name_plural = _('Perfiles de Usuario')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def get_full_name(self):
        """
        Return the full name if available, otherwise username
        """
        if self.full_name:
            return self.full_name
        return super().get_full_name() or self.username

    def has_role_permission(self, permission_codename):
        """
        Check if user has specific permission based on their role
        """
        role_permissions = self.get_role_permissions()
        return permission_codename in role_permissions

    def get_role_permissions(self):
        """
        Return list of permissions for the user's role
        SIMPLIFIED: Only 3 roles
        
        BUSINESS LOGIC:
        - Only CUSTODIANS create claims
        - ADMIN/MANAGER review and manage claims (change status, validate docs)
        - MANAGER cannot manage assets
        - ADMIN manages assets (assign to custodians)
        """
        permissions_map = {
            'admin': [
                # Full access to everything
                'users_read', 'users_write', 'users_create', 'users_update', 'users_delete', 'users_manage',
                'policies_read', 'policies_write', 'policies_create', 'policies_update', 'policies_delete', 'policies_manage',
                # Claims: READ, WRITE (review/manage), UPDATE, DELETE - NO CREATE
                'claims_read', 'claims_write', 'claims_update', 'claims_delete', 'claims_manage',
                'invoices_read', 'invoices_write', 'invoices_create', 'invoices_update', 'invoices_delete', 'invoices_manage',
                # Assets: Manage for assignment purposes
                'assets_read', 'assets_write', 'assets_create', 'assets_update', 'assets_delete', 'assets_manage',
                'reports_read', 'reports_write', 'reports_create', 'reports_update', 'reports_delete', 'reports_manage',
                'insurance_companies_read', 'insurance_companies_write', 'insurance_companies_create', 'insurance_companies_update', 'insurance_companies_delete', 'insurance_companies_manage',
                'brokers_read', 'brokers_write', 'brokers_create', 'brokers_update', 'brokers_delete', 'brokers_manage',
                'settings_read', 'settings_write', 'settings_create', 'settings_update', 'settings_delete', 'settings_manage'
            ],
            'insurance_manager': [
                # Insurance manager permissions
                'users_read',
                'policies_read', 'policies_write', 'policies_create', 'policies_update', 'policies_delete',
                # Claims: READ, WRITE (review/manage), UPDATE - NO CREATE, NO DELETE
                'claims_read', 'claims_write', 'claims_update', 'claims_manage',
                'invoices_read', 'invoices_write', 'invoices_create', 'invoices_update',
                # Assets: ONLY READ - Cannot manage assets
                'assets_read',
                'reports_read',
                'insurance_companies_read', 'insurance_companies_write', 'insurance_companies_create', 'insurance_companies_update',
                'brokers_read', 'brokers_write', 'brokers_create', 'brokers_update'
            ],
            'requester': [
                # Custodian permissions - VERY LIMITED
                # Claims: Can CREATE, READ, WRITE (edit their own)
                'claims_read', 'claims_write', 'claims_create',
                'assets_read'  # Only their own assets
            ]
        }

        return permissions_map.get(self.role, [])

    def clean(self):
        """
        Validate user data
        """
        super().clean()
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError(_('Rol inválido seleccionado'))

    def generate_reset_token(self):
        """
        Generate a password reset token
        """
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for i in range(32))
        # In a real implementation, you'd store this token with an expiry
        # For now, we'll just return it
        return token

    def soft_delete(self):
        """
        Soft delete the user by deactivating
        """
        self.is_active = False
        self.save()

    def save(self, *args, **kwargs):
        """
        Override save to perform additional validation
        """
        self.full_clean()
        super().save(*args, **kwargs)
