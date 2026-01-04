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
        is_new = self.pk is None

        if not self.claim_number:
            self.claim_number = self.generate_claim_number()

        self.full_clean()
        super().save(*args, **kwargs)

        # Send email notifications for new claims
        if is_new:
            from django.db import transaction
            transaction.on_commit(lambda: self._send_creation_notifications())

    def _send_creation_notifications(self):
        """
        Send email notifications when claim is created
        """
        try:
            from notifications.email_service import EmailService
            EmailService.send_claim_reported_notification(self)
        except Exception as e:
            # Log error but don't break the save operation
            import logging
            logging.error(f"Error sending claim creation notifications: {e}")


class ClaimDocument(models.Model):
    """
    Model for claim documents with versioning support
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

    # Document status choices
    STATUS_CHOICES = [
        ('active', _('Activo')),
        ('archived', _('Archivado')),
        ('deleted', _('Eliminado')),
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

    # Versioning fields
    version = models.PositiveIntegerField(
        _('Versión'),
        default=1
    )
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Documento padre'),
        related_name='versions'
    )
    is_latest_version = models.BooleanField(
        _('Es la versión más reciente'),
        default=True
    )

    # File fields
    file = models.FileField(
        _('Archivo'),
        upload_to='claims/documents/%Y/%m/'
    )
    file_size = models.PositiveIntegerField(
        _('Tamaño del archivo'),
        editable=False
    )
    mime_type = models.CharField(
        _('Tipo MIME'),
        max_length=100,
        blank=True
    )

    # Metadata
    description = models.TextField(
        _('Descripción'),
        blank=True
    )
    tags = models.CharField(
        _('Etiquetas'),
        max_length=500,
        blank=True,
        help_text=_('Etiquetas separadas por comas')
    )

    # Claim-specific fields
    is_required = models.BooleanField(
        _('¿Es requerido?'),
        default=False
    )
    required_deadline = models.DateField(
        _('Fecha límite'),
        null=True,
        blank=True,
        help_text=_('Fecha límite para subir este documento requerido')
    )

    # Status and audit
    status = models.CharField(
        _('Estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Subido por'),
        related_name='uploaded_claim_documents'
    )
    uploaded_at = models.DateTimeField(_('Fecha de subida'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Última modificación'), auto_now=True)

    class Meta:
        verbose_name = _('Documento de Siniestro')
        verbose_name_plural = _('Documentos de Siniestro')
        ordering = ['-uploaded_at']
        unique_together = ['claim', 'document_name', 'version']

    def __str__(self):
        version_str = f" v{self.version}" if self.version > 1 else ""
        return f"{self.document_name}{version_str} ({self.claim.claim_number})"

    def save(self, *args, **kwargs):
        """
        Override save to handle versioning and file metadata
        """
        is_new = self.pk is None

        if self.file:
            self.file_size = self.file.size
            # Try to get mime type
            try:
                import mimetypes
                self.mime_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
            except:
                self.mime_type = 'application/octet-stream'

        # Handle versioning
        if is_new and self.parent_document:
            # This is a new version of an existing document
            self.version = self.parent_document.version + 1
            # Mark previous version as not latest
            self.parent_document.is_latest_version = False
            self.parent_document.save(update_fields=['is_latest_version'])
        elif is_new:
            # First version
            self.version = 1
            self.is_latest_version = True

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
        Override delete to handle versioning and file cleanup
        """
        # If this is the latest version and there are older versions,
        # mark the previous version as latest
        if self.is_latest_version and self.parent_document:
            self.parent_document.is_latest_version = True
            self.parent_document.save(update_fields=['is_latest_version'])

        # Remove file from storage
        if self.file:
            self.file.delete(save=False)

        super().delete(*args, **kwargs)

    def get_file_extension(self):
        """Get file extension"""
        if self.file and self.file.name:
            return self.file.name.split('.')[-1].lower()
        return ''

    def get_file_icon(self):
        """Get appropriate icon based on file type"""
        ext = self.get_file_extension()
        icon_map = {
            'pdf': 'bi-file-earmark-pdf',
            'doc': 'bi-file-earmark-word',
            'docx': 'bi-file-earmark-word',
            'xls': 'bi-file-earmark-excel',
            'xlsx': 'bi-file-earmark-excel',
            'ppt': 'bi-file-earmark-ppt',
            'pptx': 'bi-file-earmark-ppt',
            'txt': 'bi-file-earmark-text',
            'jpg': 'bi-file-earmark-image',
            'jpeg': 'bi-file-earmark-image',
            'png': 'bi-file-earmark-image',
            'gif': 'bi-file-earmark-image',
        }
        return icon_map.get(ext, 'bi-file-earmark')

    def can_view_inline(self):
        """Check if file can be viewed inline in browser"""
        return self.mime_type in [
            'application/pdf',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/gif'
        ]

    def create_new_version(self, new_file, uploaded_by, description=None):
        """Create a new version of this document"""
        new_version = ClaimDocument.objects.create(
            claim=self.claim,
            document_name=self.document_name,
            document_type=self.document_type,
            parent_document=self,
            file=new_file,
            description=description or self.description,
            tags=self.tags,
            is_required=self.is_required,
            required_deadline=self.required_deadline,
            uploaded_by=uploaded_by,
            status='active'
        )

        # Mark current version as not latest
        self.is_latest_version = False
        self.save(update_fields=['is_latest_version'])

        return new_version

    @property
    def formatted_file_size(self):
        """Return formatted file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_versions(self):
        """Get all versions of this document"""
        if self.parent_document:
            # This is a version, get all versions of the root document
            root = self
            while root.parent_document:
                root = root.parent_document
            return ClaimDocument.objects.filter(
                models.Q(id=root.id) | models.Q(parent_document=root)
            ).order_by('-version')
        else:
            # This is the root document
            return ClaimDocument.objects.filter(
                models.Q(id=self.id) | models.Q(parent_document=self)
            ).order_by('-version')

    def is_overdue(self):
        """Check if required document is overdue"""
        if not self.is_required or not self.required_deadline:
            return False
        return timezone.now().date() > self.required_deadline

    @staticmethod
    def get_required_documents_for_claim(claim):
        """Get list of required documents based on claim type and status"""
        required_docs = []

        # Always required documents
        required_docs.extend([
            ('initial_report', _('Reporte inicial')),
            ('photos', _('Fotos del siniestro')),
        ])

        # Status-based requirements
        if claim.status in ['documentation_pending', 'sent_to_insurer', 'under_evaluation']:
            required_docs.extend([
                ('police_report', _('Reporte policial')),
                ('appraisal', _('Avalúo')),
            ])

        if claim.status in ['liquidated', 'paid', 'closed']:
            required_docs.extend([
                ('invoice', _('Factura')),
                ('settlement', _('Finiquito')),
            ])

        return required_docs


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


class ClaimSettlement(models.Model):
    """
    Formal settlement document for insurance claims
    """

    # Settlement status choices
    STATUS_CHOICES = [
        ('draft', _('Borrador')),
        ('pending_approval', _('Pendiente de Aprobación')),
        ('approved', _('Aprobado')),
        ('signed', _('Firmado')),
        ('paid', _('Pagado')),
        ('rejected', _('Rechazado')),
    ]

    claim = models.OneToOneField(
        Claim,
        on_delete=models.CASCADE,
        verbose_name=_('Siniestro'),
        related_name='settlement'
    )

    # Settlement identification
    settlement_number = models.CharField(
        _('Número de Finiquito'),
        max_length=50,
        unique=True,
        blank=True
    )
    claim_reference_number = models.CharField(
        _('Número de Reclamo'),
        max_length=100,
        blank=True,
        help_text=_('Número de referencia del reclamo en la aseguradora')
    )

    # Financial details
    total_claim_amount = models.DecimalField(
        _('Valor Total del Reclamo'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Monto total aprobado por la aseguradora')
    )
    deductible_amount = models.DecimalField(
        _('Deducible Aplicado'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Monto del deducible aplicado')
    )
    depreciation_amount = models.DecimalField(
        _('Depreciación'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Valor de depreciación aplicado')
    )
    final_payment_amount = models.DecimalField(
        _('Valor Final a Pagar'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Monto final que se pagará al asegurado')
    )

    # Settlement details
    settlement_date = models.DateField(
        _('Fecha de Finiquito'),
        auto_now_add=True
    )
    payment_date = models.DateField(
        _('Fecha de Pago'),
        null=True,
        blank=True
    )
    payment_reference = models.CharField(
        _('Referencia de Pago'),
        max_length=100,
        blank=True
    )

    # Status and approval
    status = models.CharField(
        _('Estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    signed_date = models.DateField(
        _('Fecha de Firma'),
        null=True,
        blank=True
    )

    # Documents
    settlement_document = models.FileField(
        _('Documento de Finiquito'),
        upload_to='settlements/',
        blank=True,
        null=True
    )

    # Audit fields
    created_at = models.DateTimeField(_('Creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado'), auto_now=True)
    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Creado por'),
        related_name='settlements_created'
    )
    approved_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Aprobado por'),
        related_name='settlements_approved'
    )

    class Meta:
        verbose_name = _('Finiquito')
        verbose_name_plural = _('Finiquitos')
        ordering = ['-created_at']

    def __str__(self):
        return f"Finiquito {self.settlement_number} - {self.claim.claim_number}"

    def save(self, *args, **kwargs):
        """
        Override save to generate settlement number and validate amounts
        """
        if not self.settlement_number:
            self.settlement_number = self.generate_settlement_number()

        # Calculate final amount if not provided
        if not self.final_payment_amount and self.total_claim_amount:
            self.final_payment_amount = (
                self.total_claim_amount -
                self.deductible_amount -
                self.depreciation_amount
            )

        self.full_clean()
        super().save(*args, **kwargs)

    def generate_settlement_number(self):
        """
        Generate unique settlement number
        """
        current_year = timezone.now().year
        last_settlement = ClaimSettlement.objects.filter(
            settlement_number__startswith=f'FIN-{current_year}-'
        ).order_by('-settlement_number').first()

        if last_settlement:
            try:
                seq_num = int(last_settlement.settlement_number.split('-')[-1])
                new_seq_num = seq_num + 1
            except (ValueError, IndexError):
                new_seq_num = 1
        else:
            new_seq_num = 1

        return f'FIN-{current_year}-{new_seq_num:06d}'

    def mark_as_signed(self):
        """
        Mark settlement as signed
        """
        self.status = 'signed'
        self.signed_date = timezone.now().date()
        self.save()

        # Send notification
        self._send_signed_notification()

    def mark_as_paid(self, payment_reference=None):
        """
        Mark settlement as paid
        """
        self.status = 'paid'
        self.payment_date = timezone.now().date()
        if payment_reference:
            self.payment_reference = payment_reference
        self.save()

        # Update claim status
        self.claim.status = 'paid'
        self.claim.payment_date = self.payment_date
        self.claim.save()

        # Send notification
        self._send_paid_notification()

    def _send_signed_notification(self):
        """
        Send notification when settlement is signed
        """
        try:
            from notifications.email_service import EmailService
            EmailService.send_email(
                template_type='settlement_signed',
                recipient_email=self.claim.reported_by.email,
                recipient_name=self.claim.reported_by.get_full_name(),
                context={
                    'user_name': self.claim.reported_by.get_full_name(),
                    'claim_number': self.claim.claim_number,
                    'settlement_number': self.settlement_number,
                    'final_amount': f"{self.final_payment_amount:.2f}",
                },
                claim=self.claim
            )
        except Exception as e:
            # Log error but don't break the process
            import logging
            logging.error(f"Error sending settlement signed notification: {e}")

    def _send_paid_notification(self):
        """
        Send notification when settlement is paid
        """
        try:
            from notifications.email_service import EmailService
            EmailService.send_email(
                template_type='payment_completed',
                recipient_email=self.claim.reported_by.email,
                recipient_name=self.claim.reported_by.get_full_name(),
                context={
                    'user_name': self.claim.reported_by.get_full_name(),
                    'claim_number': self.claim.claim_number,
                    'settlement_number': self.settlement_number,
                    'payment_amount': f"{self.final_payment_amount:.2f}",
                    'payment_date': self.payment_date.strftime('%d/%m/%Y') if self.payment_date else '',
                },
                claim=self.claim
            )
        except Exception as e:
            # Log error but don't break the process
            import logging
            logging.error(f"Error sending settlement paid notification: {e}")

    @property
    def is_overdue_for_payment(self):
        """
        Check if payment is overdue (more than 72 hours since signed)
        """
        if self.status == 'signed' and self.signed_date:
            from datetime import timedelta
            overdue_date = self.signed_date + timedelta(days=3)
            return timezone.now().date() > overdue_date
        return False
