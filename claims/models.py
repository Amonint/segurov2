from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from policies.models import Policy
from accounts.models import UserProfile

class Claim(models.Model):
    """
    Model for insurance claims with workflow management
    """

    # Claim status choices (workflow states)
    STATUS_CHOICES = [
        ('reported', _('Reportado')),
        ('documentation_pending', _('Documentación pendiente')),
        ('sent_to_insurer', _('Enviado a aseguradora')),
        ('under_evaluation', _('En evaluación')),
        ('liquidated', _('Liquidado')),
        ('paid', _('Pagado')),
        ('closed', _('Cerrado')),
        ('rejected', _('Rechazado')),
    ]

    # Claim fields
    claim_number = models.CharField(
        _('Número de siniestro'),
        max_length=50,
        unique=True
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Póliza'),
        related_name='claims'
    )

    # Incident information
    incident_date = models.DateField(_('Fecha del incidente'))
    report_date = models.DateField(_('Fecha de reporte'))
    incident_location = models.CharField(
        _('Ubicación del incidente'),
        max_length=255
    )
    incident_description = models.TextField(_('Descripción del incidente'))

    # Asset information
    asset_type = models.CharField(
        _('Tipo de bien afectado'),
        max_length=100
    )
    asset_description = models.CharField(
        _('Descripción del bien'),
        max_length=255
    )
    asset_code = models.CharField(
        _('Código del bien'),
        max_length=50,
        blank=True
    )

    # Financial information
    estimated_loss = models.DecimalField(
        _('Pérdida estimada'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Workflow status
    status = models.CharField(
        _('Estado'),
        max_length=25,
        choices=STATUS_CHOICES,
        default='reported'
    )

    # Resolution information
    approved_amount = models.DecimalField(
        _('Monto aprobado'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    payment_date = models.DateField(
        _('Fecha de pago'),
        null=True,
        blank=True
    )
    rejection_reason = models.TextField(
        _('Razón de rechazo'),
        blank=True
    )

    # Relations
    reported_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Reportado por'),
        related_name='reported_claims'
    )
    assigned_to = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Asignado a'),
        related_name='assigned_claims'
    )

    # Timestamps
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Siniestro')
        verbose_name_plural = _('Siniestros')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.claim_number} - {self.incident_description[:50]}"

    def clean(self):
        """
        Validate claim data
        """
        super().clean()

        # Validate dates
        if self.report_date and self.incident_date and self.report_date < self.incident_date:
            raise ValidationError(_('La fecha de reporte no puede ser anterior a la fecha del incidente'))

        # Validate approved amount
        if self.approved_amount and self.approved_amount > self.estimated_loss:
            raise ValidationError(_('El monto aprobado no puede ser mayor a la pérdida estimada'))

        # Validate rejection reason for rejected claims
        if self.status == 'rejected' and not self.rejection_reason:
            raise ValidationError(_('Debe proporcionar una razón de rechazo'))

        # Validate payment date for paid claims
        if self.status == 'paid' and not self.payment_date:
            raise ValidationError(_('Debe proporcionar una fecha de pago para siniestros pagados'))

    def can_change_status(self, new_status, user):
        """
        Check if user can change claim status based on role and current status
        """
        # Define valid status transitions
        transitions = {
            'reported': ['documentation_pending', 'sent_to_insurer', 'rejected'],
            'documentation_pending': ['sent_to_insurer', 'rejected'],
            'sent_to_insurer': ['under_evaluation', 'rejected'],
            'under_evaluation': ['liquidated', 'rejected'],
            'liquidated': ['paid', 'rejected'],
            'paid': ['closed'],
            'rejected': [],  # Cannot change from rejected
            'closed': []  # Cannot change from closed
        }

        if new_status not in transitions.get(self.status, []):
            return False

        # Role-based permissions for status changes
        role_permissions = {
            'requester': ['reported'],  # Can only report
            'consultant': ['reported', 'documentation_pending', 'sent_to_insurer'],
            'insurance_manager': ['reported', 'documentation_pending', 'sent_to_insurer',
                                'under_evaluation', 'liquidated', 'paid', 'closed', 'rejected'],
            'admin': ['reported', 'documentation_pending', 'sent_to_insurer',
                     'under_evaluation', 'liquidated', 'paid', 'closed', 'rejected']
        }

        return new_status in role_permissions.get(user.role, [])

    def change_status(self, new_status, user, notes=None):
        """
        Change claim status with validation and timeline creation
        """
        if not self.can_change_status(new_status, user):
            raise ValidationError(_('No tiene permisos para cambiar el estado a %(status)s') % {'status': new_status})

        old_status = self.status
        self.status = new_status
        self.save()

        # Create timeline entry
        ClaimTimeline.objects.create(
            claim=self,
            event_type='status_change',
            event_description=f'Cambio de estado: {old_status} → {new_status}',
            old_status=old_status,
            new_status=new_status,
            created_by=user
        )

        return True

    def get_days_in_current_status(self):
        """
        Get number of days claim has been in current status
        """
        # Get the most recent status change
        last_timeline = self.timeline.filter(
            event_type='status_change',
            new_status=self.status
        ).order_by('-created_at').first()

        if last_timeline:
            return (timezone.now().date() - last_timeline.created_at.date()).days
        else:
            return (timezone.now().date() - self.created_at.date()).days

    def is_overdue(self):
        """
        Check if claim is overdue based on workflow rules
        """
        days_in_status = self.get_days_in_current_status()

        # Define overdue thresholds
        overdue_thresholds = {
            'documentation_pending': 8,  # 8 days to gather documentation
            'sent_to_insurer': 30,       # 30 days for insurer evaluation
            'under_evaluation': 30,      # 30 days for evaluation
            'liquidated': 2             # 2 days to pay after liquidation
        }

        threshold = overdue_thresholds.get(self.status, 999)
        return days_in_status > threshold

    @staticmethod
    def generate_claim_number():
        """
        Generate unique claim number
        """
        current_year = timezone.now().year
        last_claim = Claim.objects.filter(
            claim_number__startswith=f'SIN-{current_year}-'
        ).order_by('-claim_number').first()

        if last_claim:
            try:
                seq_num = int(last_claim.claim_number.split('-')[-1])
                new_seq_num = seq_num + 1
            except (ValueError, IndexError):
                new_seq_num = 1
        else:
            new_seq_num = 1

        return f'SIN-{current_year}-{new_seq_num:06d}'

    def save(self, *args, **kwargs):
        """
        Override save to generate claim number and perform validation
        """
        if not self.claim_number:
            self.claim_number = self.generate_claim_number()

        self.full_clean()
        super().save(*args, **kwargs)


class ClaimDocument(models.Model):
    """
    Model for claim documents
    """

    # Document type choices
    DOCUMENT_TYPE_CHOICES = [
        ('initial_report', _('Reporte inicial')),
        ('photos', _('Fotos')),
        ('police_report', _('Reporte policial')),
        ('appraisal', _('Avalúo')),
        ('invoice', _('Factura')),
        ('settlement', _('Finiquito')),
        ('other', _('Otro')),
    ]

    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        verbose_name=_('Siniestro'),
        related_name='documents'
    )
    document_name = models.CharField(
        _('Nombre del documento'),
        max_length=255
    )
    document_type = models.CharField(
        _('Tipo de documento'),
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES
    )
    file = models.FileField(
        _('Archivo'),
        upload_to='claims/documents/%Y/%m/'
    )
    file_size = models.PositiveIntegerField(
        _('Tamaño del archivo'),
        editable=False
    )
    is_required = models.BooleanField(
        _('¿Es requerido?'),
        default=False
    )
    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Subido por'),
        related_name='uploaded_claim_documents'
    )
    uploaded_at = models.DateTimeField(_('Fecha de subida'), auto_now_add=True)

    class Meta:
        verbose_name = _('Documento de Siniestro')
        verbose_name_plural = _('Documentos de Siniestro')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document_name} ({self.claim.claim_number})"

    def save(self, *args, **kwargs):
        """
        Override save to calculate file size and create timeline entry
        """
        if self.file:
            self.file_size = self.file.size

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create timeline entry for new documents
        if is_new:
            ClaimTimeline.objects.create(
                claim=self.claim,
                event_type='document_uploaded',
                event_description=f'Documento subido: {self.document_name} ({self.document_type})',
                created_by=self.uploaded_by
            )

    def delete(self, *args, **kwargs):
        """
        Override delete to remove file from storage
        """
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)


class ClaimTimeline(models.Model):
    """
    Model for claim timeline/events
    """

    # Event type choices
    EVENT_TYPE_CHOICES = [
        ('status_change', _('Cambio de estado')),
        ('document_uploaded', _('Documento subido')),
        ('comment', _('Comentario')),
        ('alert_sent', _('Alerta enviada')),
        ('payment_received', _('Pago recibido')),
    ]

    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        verbose_name=_('Siniestro'),
        related_name='timeline'
    )
    event_type = models.CharField(
        _('Tipo de evento'),
        max_length=20,
        choices=EVENT_TYPE_CHOICES
    )
    event_description = models.TextField(_('Descripción del evento'))
    old_status = models.CharField(
        _('Estado anterior'),
        max_length=25,
        blank=True
    )
    new_status = models.CharField(
        _('Estado nuevo'),
        max_length=25,
        blank=True
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Creado por'),
        related_name='timeline_entries'
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)

    class Meta:
        verbose_name = _('Entrada de Timeline')
        verbose_name_plural = _('Timeline de Siniestros')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.claim.claim_number} - {self.event_type} ({self.created_at.date()})"
