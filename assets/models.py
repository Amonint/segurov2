from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from accounts.models import UserProfile
from policies.models import Policy

class Asset(models.Model):
    """
    Model for assets/bienes in the insurance system
    """

    # Asset type choices
    ASSET_TYPE_CHOICES = [
        ('vehiculo', _('Vehículo')),
        ('equipo_electronico', _('Equipo electrónico')),
        ('maquinaria', _('Maquinaria')),
        ('mobiliario', _('Mobiliario')),
        ('herramientas', _('Herramientas')),
        ('inventario', _('Inventario')),
        ('otros', _('Otros')),
    ]

    # Condition status choices
    CONDITION_STATUS_CHOICES = [
        ('excelente', _('Excelente')),
        ('bueno', _('Bueno')),
        ('regular', _('Regular')),
        ('malo', _('Malo')),
        ('fuera_de_servicio', _('Fuera de servicio')),
    ]

    # Asset fields
    asset_code = models.CharField(
        _('Código del activo'),
        max_length=50,
        unique=True
    )
    name = models.CharField(
        _('Nombre del bien'),
        max_length=255
    )
    description = models.TextField(
        _('Descripción'),
        blank=True
    )

    # Specifications
    brand = models.CharField(
        _('Marca'),
        max_length=100,
        blank=True
    )
    model = models.CharField(
        _('Modelo'),
        max_length=100,
        blank=True
    )
    serial_number = models.CharField(
        _('Número de serie'),
        max_length=100,
        blank=True
    )

    # Classification
    asset_type = models.CharField(
        _('Tipo de activo'),
        max_length=20,
        choices=ASSET_TYPE_CHOICES
    )
    location = models.CharField(
        _('Ubicación física'),
        max_length=255
    )

    # Financial information
    acquisition_date = models.DateField(_('Fecha de adquisición'))
    acquisition_cost = models.DecimalField(
        _('Costo de adquisición'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    current_value = models.DecimalField(
        _('Valor actual'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Status
    condition_status = models.CharField(
        _('Estado de condición'),
        max_length=20,
        choices=CONDITION_STATUS_CHOICES,
        default='bueno'
    )

    # Relations
    custodian = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Custodio'),
        related_name='custodied_assets',
        limit_choices_to={'role': 'requester'}  # Only requesters can be custodians
    )
    responsible_user = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Usuario responsable'),
        related_name='responsible_assets'
    )

    # Insurance
    is_insured = models.BooleanField(
        _('¿Está asegurado?'),
        default=False
    )
    insurance_policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Póliza de seguro'),
        related_name='insured_assets'
    )

    # Timestamps
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Activo/Bien')
        verbose_name_plural = _('Activos/Bienes')
        ordering = ['asset_code']

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    def clean(self):
        """
        Validate asset data
        """
        super().clean()

        # Validate custodian role - check if custodian exists first
        if hasattr(self, 'custodian_id') and self.custodian_id:
            if self.custodian and self.custodian.role != 'requester':
                raise ValidationError(_('El custodio debe tener el rol de "Custodio de bienes"'))

        # Validate current value - check if both values exist first
        if self.current_value is not None and self.acquisition_cost is not None:
            if self.current_value > self.acquisition_cost:
                raise ValidationError(_('El valor actual no puede ser mayor al costo de adquisición'))

        # Validate insurance policy
        if self.is_insured and not self.insurance_policy:
            raise ValidationError(_('Debe seleccionar una póliza si el activo está asegurado'))

    def calculate_depreciation(self, years=None):
        """
        Calculate depreciation (simplified straight-line method)
        """
        if not years:
            years = (timezone.now().date() - self.acquisition_date).days / 365.25

        if years <= 0:
            return self.acquisition_cost

        # Simplified: assume 10% annual depreciation for most assets
        depreciation_rate = Decimal('0.10')

        # Don't depreciate below 10% of original value
        min_value = self.acquisition_cost * Decimal('0.10')

        depreciated_value = self.acquisition_cost * (1 - depreciation_rate * Decimal(str(min(years, 10))))

        return max(depreciated_value, min_value)

    def update_current_value(self):
        """
        Update current value based on depreciation
        """
        self.current_value = self.calculate_depreciation()
        self.save()

    def has_valid_insurance(self):
        """
        Check if asset has valid insurance coverage
        """
        if not self.is_insured or not self.insurance_policy:
            return False

        return self.insurance_policy.status == 'active'
    
    def get_active_claims(self):
        """
        Retorna siniestros activos de este bien
        """
        return self.claims.exclude(status__in=['cerrado', 'rechazado'])
    
    def can_report_claim(self):
        """
        Verifica si se puede reportar un siniestro para este bien
        Returns: (bool, str) - (puede_reportar, razon_si_no)
        """
        # Debe tener seguro activo
        if not self.has_valid_insurance():
            return False, "El bien no tiene seguro activo"
        
        # No debe tener siniestros pendientes
        active_claims = self.get_active_claims()
        if active_claims.exists():
            claim_numbers = ', '.join([c.claim_number for c in active_claims[:3]])
            return False, f"Ya existe un siniestro activo: {claim_numbers}"
        
        return True, ""

    @staticmethod
    def generate_asset_code():
        """
        Generate unique asset code
        """
        current_year = timezone.now().year
        last_asset = Asset.objects.filter(
            asset_code__startswith=f'ACT-{current_year}-'
        ).order_by('-asset_code').first()

        if last_asset:
            try:
                seq_num = int(last_asset.asset_code.split('-')[-1])
                new_seq_num = seq_num + 1
            except (ValueError, IndexError):
                new_seq_num = 1
        else:
            new_seq_num = 1

        return f'ACT-{current_year}-{new_seq_num:06d}'

    def save(self, *args, **kwargs):
        """
        Override save to generate asset code and perform validation
        """
        if not self.asset_code:
            self.asset_code = self.generate_asset_code()

        # Update current value if not set
        if not self.current_value:
            self.current_value = self.acquisition_cost

        self.full_clean()
        super().save(*args, **kwargs)
