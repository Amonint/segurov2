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

    # Claim status choices (workflow states) - Enhanced for TDR
    STATUS_CHOICES = [
        ('reportado', _('Reportado')),
        ('docs_pendientes', _('Documentación pendiente')),
        ('docs_completos', _('Documentación completa')),
        ('enviado_aseguradora', _('Enviado a aseguradora')),
        ('en_revision', _('En revisión')),
        ('liquidado', _('Liquidado')),
        ('pagado', _('Pagado')),
        ('cerrado', _('Cerrado')),
        ('rechazado', _('Rechazado')),
    ]

    # Claim fields
    claim_number = models.CharField(
        _('Número de siniestro'),
        max_length=50,
        unique=True
    )
    
    # Asset relationship - NUEVO: Relación directa con el bien
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        null=True,  # Nullable for migration
        blank=True,
        verbose_name=_('Bien afectado'),
        related_name='claims',
        help_text=_('Bien al que pertenece este siniestro')
    )
    
    policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Póliza'),
        related_name='claims'
    )
    
    # Incident information - Enhanced for TDR
    fecha_siniestro = models.DateField(
        _('Fecha del siniestro'),
        help_text=_('Fecha real en que ocurrió el siniestro')
    )
    incident_date = models.DateField(
        _('Fecha del incidente'),
        help_text=_('Alias para fecha_siniestro (compatibilidad)')
    )
    fecha_notificacion = models.DateField(
        _('Fecha de notificación'),
        auto_now_add=True,
        help_text=_('Fecha en que se notifica el siniestro')
    )
    report_date = models.DateField(
        _('Fecha de reporte'),
        auto_now_add=True,
        help_text=_('Fecha en que se reporta el siniestro')
    )
    fecha_cierre = models.DateField(
        _('Fecha de cierre'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se cierra el siniestro')
    )
    
    # Detailed incident information
    causa = models.TextField(
        _('Causa del siniestro'),
        help_text=_('Descripción detallada de la causa')
    )
    ubicacion_detallada = models.TextField(
        _('Ubicación detallada'),
        help_text=_('Ubicación específica donde ocurrió el siniestro')
    )
    incident_location = models.CharField(
        _('Ubicación del incidente'),
        max_length=255,
        help_text=_('Alias para ubicacion_detallada (compatibilidad)')
    )
    incident_description = models.TextField(
        _('Descripción del incidente'),
        help_text=_('Descripción general del incidente')
    )
    
    # Coverage applied
    cobertura_aplicada = models.ForeignKey(
        'policies.Coverage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Cobertura aplicada'),
        related_name='siniestros',
        help_text=_('Cobertura de la póliza que aplica a este siniestro')
    )

    # Asset information (cached from Asset model for historical purposes)
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
        default='reportado'
    )
    
    # SLA Control dates - TDR Requirements
    fecha_solicitud_documentos = models.DateField(
        _('Fecha solicitud documentos'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se solicitan documentos al reportante')
    )
    fecha_docs_completos = models.DateField(
        _('Fecha documentos completos'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se completa la documentación')
    )
    fecha_envio_aseguradora = models.DateField(
        _('Fecha envío aseguradora'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se envía a la aseguradora')
    )
    fecha_respuesta_aseguradora = models.DateField(
        _('Fecha respuesta aseguradora'),
        null=True,
        blank=True,
        help_text=_('Fecha en que responde la aseguradora')
    )
    
    # SLA Limits
    dias_limite_documentos = models.PositiveIntegerField(
        _('Días límite documentos'),
        default=30,
        help_text=_('Días límite máximo para completar documentación')
    )
    dias_limite_respuesta_aseguradora = models.PositiveIntegerField(
        _('Días hábiles respuesta aseguradora'),
        default=8,
        help_text=_('Días hábiles para respuesta de aseguradora')
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

    # Relations - Enhanced for TDR
    reportante = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Reportante'),
        related_name='siniestros_reportados',
        help_text=_('Usuario que reporta el siniestro')
    )
    reported_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Reportado por'),
        related_name='reported_claims',
        help_text=_('Alias para reportante (compatibilidad)')
    )
    assigned_to = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Asignado a'),
        related_name='assigned_claims'
    )
    
    # Notification tracking
    broker_notificado = models.ForeignKey(
        'brokers.Broker',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Broker notificado'),
        help_text=_('Broker al que se notificó el siniestro')
    )
    aseguradora_notificada = models.ForeignKey(
        'companies.InsuranceCompany',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Aseguradora notificada'),
        help_text=_('Aseguradora a la que se notificó')
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

        # Role-based permissions for status changes (SIMPLIFIED TO 3 ROLES)
        role_permissions = {
            'requester': ['reported'],  # Can only report
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
            event_description=f'Cambio de estado: {old_status} -> {new_status}',
            old_status=old_status,
            new_status=new_status,
            created_by=user,
            notes=notes  # Assuming ClaimTimeline has a notes field, if not we might need to add it or append to description
        )

        # --- TDR Notification Logic ---
        from notifications.models import Notification
        
        # Determine notification recipient (usually the reporter/custodian)
        recipient = self.reported_by
        
        if recipient and recipient != user: # Don't notify self
            if new_status == 'docs_pendientes':
                Notification.create_notification(
                    user=recipient,
                    notification_type='document_required',
                    title=f'Corrección Requerida: Siniestro {self.claim_number}',
                    message=f'Se requiere documentación adicional o correcciones para su siniestro. Nota: {notes or "Sin notas adicionales."}',
                    priority='high',
                    link=f'/claims/{self.pk}/'
                )
            elif new_status == 'rechazado':
                Notification.create_notification(
                    user=recipient,
                    notification_type='alert',
                    title=f'Siniestro Rechazado: {self.claim_number}',
                    message=f'Su siniestro ha sido rechazado. Razón: {notes or "Contacte a administración."}',
                    priority='urgent',
                    link=f'/claims/{self.pk}/'
                )
            elif new_status == 'enviado_aseguradora':
                 Notification.create_notification(
                    user=recipient,
                    notification_type='claim_update',
                    title=f'Siniestro en Trámite: {self.claim_number}',
                    message=f'Su siniestro ha sido validado y enviado a la aseguradora.',
                    priority='normal',
                    link=f'/claims/{self.pk}/'
                )
            elif new_status == 'pagado':
                 Notification.create_notification(
                    user=recipient,
                    notification_type='claim_update',
                    title=f'Siniestro Pagado: {self.claim_number}',
                    message=f'El pago de su siniestro ha sido procesado.',
                    priority='normal',
                    link=f'/claims/{self.pk}/'
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
            'docs_pendientes': 8,  # 8 days to gather documentation
            'enviado_aseguradora': 30,       # 30 days for insurer evaluation
            'en_revision': 30,      # 30 days for evaluation
            'liquidado': 2             # 2 days to pay after liquidation
        }

        threshold = overdue_thresholds.get(self.status, 999)
        return days_in_status > threshold
    
    def verificar_sla_documentos(self):
        """
        Verifica si se excedió el plazo de documentación (8 días)
        Requisito TDR: Control de plazos de documentación
        """
        if self.fecha_solicitud_documentos and not self.fecha_docs_completos:
            dias = (timezone.now().date() - self.fecha_solicitud_documentos).days
            return dias > 8
        return False
    
    def verificar_sla_respuesta_aseguradora(self):
        """
        Verifica si se excedió el plazo de respuesta de aseguradora (8 días hábiles)
        Requisito TDR: Control de respuesta aseguradora
        """
        if self.fecha_envio_aseguradora and not self.fecha_respuesta_aseguradora:
            # Calcular días hábiles (simplificado: días totales * 5/7)
            dias_totales = (timezone.now().date() - self.fecha_envio_aseguradora).days
            dias_habiles = int(dias_totales * 5 / 7)  # Aproximación
            return dias_habiles > 8
        return False
    
    def verificar_limite_maximo_30_dias(self):
        """
        Verifica si se excedió el límite máximo de 30 días para documentación
        Requisito TDR: Límite máximo absoluto
        """
        if self.fecha_solicitud_documentos and not self.fecha_docs_completos:
            dias = (timezone.now().date() - self.fecha_solicitud_documentos).days
            return dias > self.dias_limite_documentos
        return False

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
        Auto-fill asset information from related asset
        """
        is_new = self.pk is None

        if not self.claim_number:
            self.claim_number = self.generate_claim_number()
        
        # Auto-fill asset information from the related asset
        if self.asset:
            self.asset_type = self.asset.asset_type
            self.asset_description = self.asset.name
            self.asset_code = self.asset.asset_code
            
            # Auto-fill policy from asset if not set
            if not self.policy and self.asset.insurance_policy:
                self.policy = self.asset.insurance_policy
            
            # Auto-fill incident_date and incident_location aliases
            if not self.incident_date:
                self.incident_date = self.fecha_siniestro
            if not self.incident_location:
                self.incident_location = self.ubicacion_detallada[:255] if self.ubicacion_detallada else ''

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
    notes = models.TextField(
        _('Notas/Observaciones'),
        blank=True,
        help_text=_('Notas adicionales sobre el cambio de estado')
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
    numero_reclamo = models.CharField(
        _('Número de reclamo aseguradora'),
        max_length=100,
        help_text=_('Número de reclamo asignado por la aseguradora')
    )
    claim_reference_number = models.CharField(
        _('Número de Reclamo'),
        max_length=100,
        blank=True,
        help_text=_('Número de referencia del reclamo en la aseguradora (alias)')
    )

    # Financial details - Enhanced for TDR
    valor_total_reclamo = models.DecimalField(
        _('Valor total del reclamo'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Monto total reclamado')
    )
    total_claim_amount = models.DecimalField(
        _('Valor Total del Reclamo'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Monto total aprobado por la aseguradora (alias)')
    )
    deducible_aplicado = models.DecimalField(
        _('Deducible aplicado'),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_('Monto del deducible aplicado según cobertura')
    )
    deductible_amount = models.DecimalField(
        _('Deducible Aplicado'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Monto del deducible aplicado (alias)')
    )
    depreciacion = models.DecimalField(
        _('Depreciación'),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_('Valor de depreciación aplicado al bien')
    )
    depreciation_amount = models.DecimalField(
        _('Depreciación'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Valor de depreciación aplicado (alias)')
    )
    valor_a_pagar = models.DecimalField(
        _('Valor final a pagar'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Valor total - deducible - depreciación')
    )
    final_payment_amount = models.DecimalField(
        _('Valor Final a Pagar'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Monto final que se pagará al asegurado (alias)')
    )

    # Settlement details - Enhanced for TDR (72-hour control)
    fecha_recepcion_finiquito = models.DateField(
        _('Fecha recepción finiquito'),
        help_text=_('Fecha en que se recibe el finiquito de la aseguradora')
    )
    settlement_date = models.DateField(
        _('Fecha de Finiquito'),
        auto_now_add=True,
        help_text=_('Fecha de creación del finiquito (alias)')
    )
    fecha_firma = models.DateField(
        _('Fecha de firma'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se firma el finiquito')
    )
    signed_date = models.DateField(
        _('Fecha de Firma'),
        null=True,
        blank=True,
        help_text=_('Fecha de firma (alias)')
    )
    fecha_limite_pago = models.DateField(
        _('Fecha límite pago (72h)'),
        editable=False,
        null=True,
        blank=True,
        help_text=_('Fecha límite para pago (72 horas desde firma)')
    )
    fecha_pago = models.DateField(
        _('Fecha pago real'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se realizó el pago')
    )
    payment_date = models.DateField(
        _('Fecha de Pago'),
        null=True,
        blank=True,
        help_text=_('Fecha de pago (alias)')
    )
    payment_reference = models.CharField(
        _('Referencia de Pago'),
        max_length=100,
        blank=True
    )
    
    # Financial management notification - TDR Requirement
    notificado_gerencia_financiera = models.BooleanField(
        _('Notificado a gerencia financiera'),
        default=False,
        help_text=_('Si se notificó a gerencia sobre deducible a cobrar')
    )
    fecha_notificacion_gerencia = models.DateTimeField(
        _('Fecha notificación gerencia'),
        null=True,
        blank=True,
        help_text=_('Fecha en que se notificó a gerencia financiera')
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
        Enhanced for TDR: 72-hour payment control and financial notification
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
        
        # Sync alias fields
        if not self.valor_a_pagar:
            self.valor_a_pagar = self.final_payment_amount
        if not self.valor_total_reclamo:
            self.valor_total_reclamo = self.total_claim_amount
        if not self.deducible_aplicado:
            self.deducible_aplicado = self.deductible_amount
        if not self.depreciacion:
            self.depreciacion = self.depreciation_amount
        
        # TDR Requirement: Calculate 72-hour payment deadline from signature
        if self.fecha_firma and not self.fecha_limite_pago:
            from datetime import timedelta
            self.fecha_limite_pago = self.fecha_firma + timedelta(days=3)
        
        # Sync signed_date alias
        if self.fecha_firma and not self.signed_date:
            self.signed_date = self.fecha_firma

        self.full_clean()
        super().save(*args, **kwargs)
        
        # TDR Requirement: Notify financial management about deductible
        if self.deducible_aplicado > 0 and not self.notificado_gerencia_financiera:
            self.notificar_gerencia_financiera()
    
    def notificar_gerencia_financiera(self):
        """
        Notifica a gerencia financiera sobre deducible a cobrar
        Requisito TDR: Notificación automática de deducibles
        """
        try:
            from notifications.email_service import EmailService
            EmailService.send_deductible_notification(self)
            self.notificado_gerencia_financiera = True
            self.fecha_notificacion_gerencia = timezone.now()
            self.save(update_fields=['notificado_gerencia_financiera', 'fecha_notificacion_gerencia'])
        except Exception as e:
            import logging
            logging.error(f"Error notificando gerencia financiera: {e}")

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
