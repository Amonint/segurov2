from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import UserProfile

class Notification(models.Model):
    """
    Model for system notifications
    """

    # Notification type choices
    NOTIFICATION_TYPE_CHOICES = [
        ('policy_expiring', _('Póliza por vencer')),
        ('payment_due', _('Pago pendiente')),
        ('claim_update', _('Actualización de siniestro')),
        ('document_required', _('Documento requerido')),
        ('alert', _('Alerta general')),
    ]

    # Priority choices
    PRIORITY_CHOICES = [
        ('low', _('Baja')),
        ('normal', _('Normal')),
        ('high', _('Alta')),
        ('urgent', _('Urgente')),
    ]

    # Notification fields
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        verbose_name=_('Usuario'),
        related_name='notifications'
    )
    notification_type = models.CharField(
        _('Tipo de notificación'),
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(
        _('Título'),
        max_length=255
    )
    message = models.TextField(_('Mensaje'))
    link = models.URLField(
        _('Enlace'),
        blank=True
    )
    is_read = models.BooleanField(
        _('¿Leída?'),
        default=False
    )
    priority = models.CharField(
        _('Prioridad'),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)

    class Meta:
        verbose_name = _('Notificación')
        verbose_name_plural = _('Notificaciones')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read', 'priority']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

    def mark_as_read(self):
        """
        Mark notification as read
        """
        if not self.is_read:
            self.is_read = True
            self.save()

    @staticmethod
    def create_notification(user, notification_type, title, message, priority='normal', link=None):
        """
        Create a new notification
        """
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            link=link
        )

    @staticmethod
    def get_unread_count(user):
        """
        Get count of unread notifications for a user
        """
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def bulk_mark_as_read(user, notification_ids=None):
        """
        Mark multiple notifications as read
        """
        queryset = Notification.objects.filter(user=user, is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        return queryset.update(is_read=True)
