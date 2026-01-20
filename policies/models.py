from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from companies.models import InsuranceCompany
from brokers.models import Broker
from accounts.models import UserProfile
import uuid

class Policy(models.Model):
    """
    Model for insurance policies
    """

    # Group type choices
    GROUP_TYPE_CHOICES = [
        ('patrimoniales', _('Patrimoniales')),
        ('personas', _('Personas')),
    ]

    # Status choices
    STATUS_CHOICES = [
        ('active', _('Activa')),
        ('expired', _('Vencida')),
        ('cancelled', _('Cancelada')),
        ('renewed', _('Renovada')),
    ]

    # Policy fields
    policy_number = models.CharField(
        _('Número de póliza'),
        max_length=50,
        unique=True
    )
    insurance_company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.PROTECT,
        verbose_name=_('Compañía de seguros'),
        related_name='policies'
    )
    broker = models.ForeignKey(
        Broker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Corredor'),
        related_name='policies'
    )

    # Classification
    group_type = models.CharField(
        _('Tipo de grupo'),
        max_length=20,
        choices=GROUP_TYPE_CHOICES
    )
    subgroup = models.CharField(
        _('Subgrupo'),
        max_length=100
    )
    branch = models.CharField(
        _('Rama'),
        max_length=100
    )

    # Dates
    start_date = models.DateField(_('Fecha de inicio'))
    end_date = models.DateField(_('Fecha de fin'))
    issue_date = models.DateField(
        _('Fecha de emisión'),
        null=True,
        blank=True
    )
    
    # Renewal control
    fecha_renovacion = models.DateField(
        _('Fecha de renovación'),
        null=True,
        blank=True,
        help_text=_('Fecha planificada para renovación de la póliza')
    )
    alerta_vencimiento_dias = models.PositiveIntegerField(
        _('Días de alerta antes del vencimiento'),
        default=30,
        help_text=_('Días antes del vencimiento para generar alerta')
    )

    # Object insured
    objeto_asegurado = models.CharField(
        _('Objeto asegurado'),
        max_length=255,
        help_text=_('Descripción del objeto o bien asegurado')
    )

    # Financial - Base values
    prima = models.DecimalField(
        _('Prima base'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Prima base de la póliza')
    )
    costo_servicio = models.DecimalField(
        _('Costo de servicio'),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_('Costo adicional de servicio')
    )
    insured_value = models.DecimalField(
        _('Valor asegurado'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Valor total asegurado')
    )

    # Financial - Tax breakdown (calculated automatically)
    contrib_superintendencia = models.DecimalField(
        _('Contribución Superintendencia (3.5%)'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Calculado automáticamente: 3.5% de la prima')
    )
    contrib_seguro_campesino = models.DecimalField(
        _('Contribución Seguro Campesino (0.5%)'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Calculado automáticamente: 0.5% de la prima')
    )
    derecho_emision = models.DecimalField(
        _('Derecho de emisión'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Calculado automáticamente según tabla de derechos')
    )
    base_imponible = models.DecimalField(
        _('Base imponible'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Prima + contribuciones + derecho emisión')
    )
    iva = models.DecimalField(
        _('IVA (15%)'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Calculado automáticamente: 15% de base imponible')
    )
    total_facturado = models.DecimalField(
        _('Total facturado'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0,
        help_text=_('Base imponible + IVA - retenciones')
    )
    retencion = models.DecimalField(
        _('Retención'),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_('Retenciones aplicables')
    )

    # Billing modality
    MODALIDAD_FACTURACION_CHOICES = [
        ('mensual', _('Mensual')),
        ('trimestral', _('Trimestral')),
        ('semestral', _('Semestral')),
        ('anual', _('Anual')),
    ]
    modalidad_facturacion = models.CharField(
        _('Modalidad de facturación'),
        max_length=20,
        choices=MODALIDAD_FACTURACION_CHOICES,
        default='anual',
        help_text=_('Frecuencia de facturación de la póliza')
    )

    # Additional info
    coverage_description = models.TextField(
        _('Descripción de cobertura'),
        blank=True
    )
    observations = models.TextField(
        _('Observaciones'),
        blank=True
    )

    # Status
    status = models.CharField(
        _('Estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Relations
    responsible_user = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Usuario responsable'),
        related_name='responsible_policies'
    )

    # Timestamps
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Póliza')
        verbose_name_plural = _('Pólizas')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.policy_number} - {self.insurance_company.name}"

    def calcular_valores_fiscales(self):
        """
        Calcula automáticamente todos los valores fiscales de la póliza
        según los requisitos del TDR
        """
        from decimal import Decimal
        from companies.models import EmissionRights
        
        # 1. Contribución Superintendencia (3.5% de prima)
        self.contrib_superintendencia = (self.prima * Decimal('0.035')).quantize(Decimal('0.01'))
        
        # 2. Contribución Seguro Campesino (0.5% de prima)
        self.contrib_seguro_campesino = (self.prima * Decimal('0.005')).quantize(Decimal('0.01'))
        
        # 3. Derecho de emisión (según tabla configurable)
        self.derecho_emision = EmissionRights.objects.get_emission_right(self.prima)
        
        # 4. Base imponible = prima + contribuciones + derecho emisión
        self.base_imponible = (
            self.prima +
            self.contrib_superintendencia +
            self.contrib_seguro_campesino +
            self.derecho_emision
        )
        
        # 5. IVA (15% sobre base imponible)
        self.iva = (self.base_imponible * Decimal('0.15')).quantize(Decimal('0.01'))
        
        # 6. Total facturado = base imponible + IVA - retenciones
        self.total_facturado = self.base_imponible + self.iva - self.retencion

    def clean(self):
        """
        Validate policy data
        """
        super().clean()

        # Validate required fields
        if not self.objeto_asegurado:
            raise ValidationError(_('El objeto asegurado es obligatorio'))

        if not self.prima or self.prima <= 0:
            raise ValidationError(_('La prima debe ser mayor a cero'))

        # Validate dates
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio'))

        # Validate insured value
        if self.insured_value <= 0:
            raise ValidationError(_('El valor asegurado debe ser mayor a cero'))

    @staticmethod
    def generate_policy_number():
        """
        Generate unique policy number
        """
        # Generate based on current year and sequential number
        current_year = timezone.now().year
        last_policy = Policy.objects.filter(
            policy_number__startswith=f'POL-{current_year}-'
        ).order_by('-policy_number').first()

        if last_policy:
            # Extract sequential number and increment
            try:
                seq_num = int(last_policy.policy_number.split('-')[-1])
                new_seq_num = seq_num + 1
            except (ValueError, IndexError):
                new_seq_num = 1
        else:
            new_seq_num = 1

        return f'POL-{current_year}-{new_seq_num:06d}'

    def is_expiring_soon(self, days=30):
        """
        Check if policy is expiring within specified days
        """
        if self.end_date:
            days_until_expiry = (self.end_date - timezone.now().date()).days
            return 0 <= days_until_expiry <= days
        return False

    def renew_policy(self, new_end_date=None):
        """
        Renew the policy
        """
        if not new_end_date:
            # Extend by one year from current end date
            new_end_date = self.end_date.replace(year=self.end_date.year + 1)

        # Create new policy with renewed status
        renewed_policy = Policy.objects.create(
            policy_number=self.generate_policy_number(),
            insurance_company=self.insurance_company,
            broker=self.broker,
            group_type=self.group_type,
            subgroup=self.subgroup,
            branch=self.branch,
            start_date=self.end_date,
            end_date=new_end_date,
            insured_value=self.insured_value,
            coverage_description=self.coverage_description,
            observations=self.observations,
            responsible_user=self.responsible_user,
            status='active'
        )

        # Update current policy status
        self.status = 'renewed'
        self.save()

        return renewed_policy

    def save(self, *args, **kwargs):
        """
        Override save to generate policy number and perform validation
        """
        if not self.policy_number:
            self.policy_number = self.generate_policy_number()
        
        # Calculate fiscal values automatically if prima is set
        if self.prima and self.prima > 0:
            self.calcular_valores_fiscales()

        self.full_clean()
        super().save(*args, **kwargs)


class PolicyDocument(models.Model):
    """
    Model for policy documents with versioning support
    """

    # Document type choices
    DOCUMENT_TYPE_CHOICES = [
        ('policy', _('Póliza')),
        ('endorsement', _('Endoso')),
        ('certificate', _('Certificado')),
        ('receipt', _('Recibo')),
        ('other', _('Otro')),
    ]

    # Document status choices
    STATUS_CHOICES = [
        ('active', _('Activo')),
        ('archived', _('Archivado')),
        ('deleted', _('Eliminado')),
    ]

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        verbose_name=_('Póliza'),
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
        upload_to='policies/documents/%Y/%m/'
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
        related_name='uploaded_policy_documents'
    )
    uploaded_at = models.DateTimeField(_('Fecha de subida'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Última modificación'), auto_now=True)

    class Meta:
        verbose_name = _('Documento de Póliza')
        verbose_name_plural = _('Documentos de Póliza')
        ordering = ['-uploaded_at']
        unique_together = ['policy', 'document_name', 'version']

    def __str__(self):
        version_str = f" v{self.version}" if self.version > 1 else ""
        return f"{self.document_name}{version_str} ({self.policy.policy_number})"

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
        new_version = PolicyDocument.objects.create(
            policy=self.policy,
            document_name=self.document_name,
            document_type=self.document_type,
            parent_document=self,
            file=new_file,
            description=description or self.description,
            tags=self.tags,
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
            return PolicyDocument.objects.filter(
                models.Q(id=root.id) | models.Q(parent_document=root)
            ).order_by('-version')
        else:
            # This is the root document
            return PolicyDocument.objects.filter(
                models.Q(id=self.id) | models.Q(parent_document=self)
            ).order_by('-version')

    @staticmethod
    def get_document_types_for_policy(policy):
        """Get available document types based on policy type"""
        base_types = ['policy', 'receipt', 'other']

        if policy.group_type == 'patrimoniales':
            base_types.extend(['certificate', 'endorsement'])
        elif policy.group_type == 'personas':
            base_types.extend(['certificate', 'endorsement'])

        return [(doc_type, dict(PolicyDocument.DOCUMENT_TYPE_CHOICES)[doc_type])
                for doc_type in base_types]


class Coverage(models.Model):
    """
    Coberturas específicas de una póliza
    Permite detallar las diferentes coberturas que incluye una póliza
    """
    
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        verbose_name=_('Póliza'),
        related_name='coberturas'
    )
    nombre = models.CharField(
        _('Nombre de la cobertura'),
        max_length=255,
        help_text=_('Ej: Daños materiales, Robo, Incendio, etc.')
    )
    descripcion = models.TextField(
        _('Descripción'),
        blank=True,
        help_text=_('Descripción detallada de la cobertura')
    )
    valor_asegurado = models.DecimalField(
        _('Valor asegurado'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Monto máximo cubierto por esta cobertura')
    )
    deducible = models.DecimalField(
        _('Deducible (monto fijo)'),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_('Monto fijo de deducible')
    )
    porcentaje_deducible = models.DecimalField(
        _('Deducible (%)'),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Porcentaje de deducible sobre el valor del siniestro')
    )
    is_active = models.BooleanField(
        _('Activa'),
        default=True,
        help_text=_('Si la cobertura está activa')
    )
    
    # Audit fields
    created_at = models.DateTimeField(_('Creada'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizada'), auto_now=True)
    
    class Meta:
        verbose_name = _('Cobertura')
        verbose_name_plural = _('Coberturas')
        ordering = ['policy', 'nombre']
        unique_together = ['policy', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.policy.policy_number}"
    
    def calcular_deducible(self, valor_siniestro):
        """
        Calcula el deducible aplicable para un siniestro
        Retorna el mayor entre el deducible fijo y el porcentual
        """
        from decimal import Decimal
        
        deducible_fijo = self.deducible
        deducible_porcentual = valor_siniestro * (self.porcentaje_deducible / Decimal('100'))
        
        return max(deducible_fijo, deducible_porcentual)
    
    def clean(self):
        """Validate coverage data"""
        super().clean()
        
        if self.valor_asegurado <= 0:
            raise ValidationError(_('El valor asegurado debe ser mayor a cero'))
        
        if self.deducible < 0:
            raise ValidationError(_('El deducible no puede ser negativo'))
        
        if self.porcentaje_deducible < 0 or self.porcentaje_deducible > 100:
            raise ValidationError(_('El porcentaje de deducible debe estar entre 0 y 100'))

