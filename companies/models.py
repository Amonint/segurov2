from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class InsuranceCompany(models.Model):
    """
    Model for insurance companies
    """
    name = models.CharField(
        _('Nombre'),
        max_length=255,
        unique=True
    )
    ruc = models.CharField(
        _('RUC'),
        max_length=13,
        unique=True,
        help_text=_('Registro Único de Contribuyentes')
    )
    address = models.TextField(
        _('Dirección'),
        blank=True
    )
    phone = models.CharField(
        _('Teléfono'),
        max_length=20,
        blank=True
    )
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    contact_person = models.CharField(
        _('Persona de contacto'),
        max_length=255,
        blank=True
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Compañía de Seguros')
        verbose_name_plural = _('Compañías de Seguros')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """
        Validate RUC format (Ecuadorian format)
        """
        super().clean()
        if self.ruc and len(self.ruc) != 13:
            raise ValidationError(_('El RUC debe tener exactamente 13 dígitos'))

    def save(self, *args, **kwargs):
        """
        Override save to perform validation
        """
        self.full_clean()
        super().save(*args, **kwargs)


class EmissionRights(models.Model):
    """
    Model for emission rights table used in invoice calculations
    """
    min_amount = models.DecimalField(
        _('Monto mínimo'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Monto mínimo del rango')
    )
    max_amount = models.DecimalField(
        _('Monto máximo'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Monto máximo del rango')
    )
    emission_right = models.DecimalField(
        _('Derecho de emisión'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Valor del derecho de emisión para este rango')
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)

    class Meta:
        verbose_name = _('Derecho de Emisión')
        verbose_name_plural = _('Derechos de Emisión')
        ordering = ['min_amount']

    def __str__(self):
        return ".2f"

    @staticmethod
    def get_emission_right(amount):
        """
        Calculate emission right for a given amount
        """
        try:
            # Find the range that contains the amount
            right = EmissionRights.objects.filter(
                min_amount__lte=amount,
                max_amount__gte=amount
            ).first()

            if right:
                return right.emission_right
            else:
                # If no range found, return 0 or raise an error
                return 0
        except EmissionRights.DoesNotExist:
            return 0

    def clean(self):
        """
        Validate emission rights ranges
        """
        super().clean()

        # Check for overlapping ranges
        overlapping = EmissionRights.objects.filter(
            models.Q(min_amount__lte=self.max_amount, max_amount__gte=self.min_amount) &
            ~models.Q(pk=self.pk)  # Exclude self if updating
        )

        if overlapping.exists():
            raise ValidationError(_('Los rangos de montos no pueden solaparse'))

        # Validate min_amount < max_amount
        if self.min_amount >= self.max_amount:
            raise ValidationError(_('El monto mínimo debe ser menor al monto máximo'))

    def save(self, *args, **kwargs):
        """
        Override save to perform validation
        """
        self.full_clean()
        super().save(*args, **kwargs)
