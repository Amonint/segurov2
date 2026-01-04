from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from accounts.models import UserProfile
import uuid

class AuditLog(models.Model):
    """
    Comprehensive audit log for all system operations
    """

    # Action type choices
    ACTION_TYPE_CHOICES = [
        ('create', _('Crear')),
        ('update', _('Actualizar')),
        ('delete', _('Eliminar')),
        ('login', _('Inicio de sesión')),
        ('logout', _('Cierre de sesión')),
        ('export', _('Exportación')),
        ('status_change', _('Cambio de estado')),
        ('payment', _('Pago')),
        ('document_upload', _('Subida de documento')),
    ]

    # Entity type choices
    ENTITY_TYPE_CHOICES = [
        ('policy', _('Póliza')),
        ('claim', _('Siniestro')),
        ('invoice', _('Factura')),
        ('asset', _('Activo')),
        ('user', _('Usuario')),
        ('insurance_company', _('Compañía aseguradora')),
        ('broker', _('Corredor')),
        ('notification', _('Notificación')),
    ]

    # Audit log fields
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Usuario'),
        related_name='audit_logs'
    )

    action_type = models.CharField(
        _('Tipo de acción'),
        max_length=20,
        choices=ACTION_TYPE_CHOICES
    )

    entity_type = models.CharField(
        _('Tipo de entidad'),
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )

    entity_id = models.CharField(
        _('ID de la entidad'),
        max_length=100,
        help_text=_('ID de la entidad afectada')
    )

    # Generic foreign key for future extensibility (optional)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Change tracking
    old_values = models.JSONField(
        _('Valores anteriores'),
        null=True,
        blank=True,
        help_text=_('JSON con los valores anteriores del registro')
    )
    new_values = models.JSONField(
        _('Valores nuevos'),
        null=True,
        blank=True,
        help_text=_('JSON con los valores nuevos del registro')
    )

    # Additional information
    description = models.TextField(
        _('Descripción'),
        help_text=_('Descripción detallada de la acción realizada')
    )

    # Request information
    ip_address = models.GenericIPAddressField(
        _('Dirección IP'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _('User Agent'),
        null=True,
        blank=True,
        help_text=_('Información del navegador/dispositivo del usuario')
    )

    # Timestamp
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)

    class Meta:
        verbose_name = _('Log de Auditoría')
        verbose_name_plural = _('Logs de Auditoría')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Sistema'
        return f"{user_name} - {self.action_type} - {self.entity_type} ({self.created_at})"

    @staticmethod
    def log_action(user, action_type, entity_type, entity_id, description,
                   old_values=None, new_values=None, ip_address=None, user_agent=None):
        """
        Create an audit log entry
        """
        return AuditLog.objects.create(
            user=user,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def get_entity_changes(old_instance, new_instance):
        """
        Compare two instances and return changed fields
        """
        if not old_instance or not new_instance:
            return None

        changes = {}
        for field in new_instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(new_instance, field_name, None)

            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None
                }

        return changes if changes else None
