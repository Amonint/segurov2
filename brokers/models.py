from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Broker(models.Model):
    """
    Model for insurance brokers
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
    commission_percentage = models.DecimalField(
        _('Porcentaje de comisión'),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Porcentaje de comisión (0-100%)')
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True
    )
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Corredor')
        verbose_name_plural = _('Corredores')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.commission_percentage}%)"

    def clean(self):
        """
        Validate broker data
        """
        super().clean()

        # Validate RUC format
        if self.ruc and len(self.ruc) != 13:
            raise ValidationError(_('El RUC debe tener exactamente 13 dígitos'))

        # Validate commission percentage
        if self.commission_percentage < 0 or self.commission_percentage > 100:
            raise ValidationError(_('El porcentaje de comisión debe estar entre 0 y 100'))

    def save(self, *args, **kwargs):
        """
        Override save to perform validation
        """
        self.full_clean()
        super().save(*args, **kwargs)
