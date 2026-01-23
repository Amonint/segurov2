from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class InsuranceCompany(models.Model):
    """
    Insurance company model
    """

    name = models.CharField(_("Nombre"), max_length=255, unique=True)
    ruc = models.CharField(
        _("RUC"),
        max_length=13,
        unique=True,
        help_text=_("Registro Único de Contribuyentes"),
    )
    address = models.TextField(_("Dirección"), blank=True)
    phone = models.CharField(_("Teléfono"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    contact_person = models.CharField(
        _("Persona de contacto"), max_length=255, blank=True
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Compañía de Seguros")
        verbose_name_plural = _("Compañías de Seguros")
        ordering = ["name"]

    def __str__(self):
        return self.name


class EmissionRightsManager(models.Manager):
    """Manager for EmissionRights with utility methods"""

    def get_emission_right(self, premium_amount):
        """Get emission right for a given premium amount"""
        try:
            right = self.filter(
                min_amount__lte=premium_amount, max_amount__gte=premium_amount
            ).first()

            if right:
                return right.emission_right
            return Decimal("0.00")
        except Exception:
            return Decimal("0.00")


class EmissionRights(models.Model):
    """
    Table for emission rights configuration by premium range
    """

    min_amount = models.DecimalField(
        _("Monto mínimo"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Monto mínimo del rango (incluyente)"),
    )
    max_amount = models.DecimalField(
        _("Monto máximo"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Monto máximo del rango (incluyente)"),
    )
    emission_right = models.DecimalField(
        _("Derecho de emisión"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Valor del derecho de emisión para este rango"),
    )
    is_active = models.BooleanField(
        _("Activo"), default=True, help_text=_("Si está activo para cálculos")
    )
    valid_from = models.DateField(
        _("Válido desde"),
        default=timezone.now,
        help_text=_("Fecha desde la cual aplica esta configuración"),
    )
    valid_until = models.DateField(
        _("Válido hasta"),
        null=True,
        blank=True,
        help_text=_("Fecha hasta la cual aplica (opcional)"),
    )
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)
    created_by = models.ForeignKey(
        "accounts.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Creado por"),
        related_name="emission_rights_created",
    )

    objects = EmissionRightsManager()

    class Meta:
        verbose_name = _("Derecho de Emisión")
        verbose_name_plural = _("Derechos de Emisión")
        ordering = ["min_amount", "valid_from"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_amount__gt=models.F("min_amount")),
                name="emission_rights_min_less_than_max",
            ),
            models.CheckConstraint(
                condition=models.Q(emission_right__gte=0),
                name="emission_rights_positive",
            ),
        ]

    def __str__(self):
        return f"${self.min_amount} - ${self.max_amount}: ${self.emission_right}"

    def clean(self):
        """
        Validate emission rights data
        """
        super().clean()

        # Validate date range
        if self.valid_until and self.valid_from >= self.valid_until:
            raise ValidationError(
                _("La fecha de inicio debe ser anterior a la fecha de fin.")
            )

        # Check for overlapping ranges (only active ones)
        if self.is_active:
            overlapping = EmissionRights.objects.filter(
                is_active=True,
                valid_from__lte=self.valid_until or timezone.now().date(),
                valid_until__gte=self.valid_from,
            ).exclude(pk=self.pk)

            # Check for range overlaps
            for existing in overlapping:
                if (
                    self.min_amount <= existing.max_amount
                    and self.max_amount >= existing.min_amount
                ):
                    raise ValidationError(
                        _(
                            "Los rangos de montos no pueden solaparse con configuraciones activas."
                        )
                    )

    def save(self, *args, **kwargs):
        """
        Override save to perform validation
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_currently_valid(self):
        """Check if this configuration is currently valid"""
        today = timezone.now().date()
        return (
            self.valid_from <= today
            and (self.valid_until is None or self.valid_until >= today)
            and self.is_active
        )


class RetentionType(models.Model):
    """
    Types of retentions that can be applied
    """

    RETENTION_TYPES = [
        ("iva", _("IVA")),
        ("islr", _("Impuesto sobre la Renta")),
        ("fonacide", _("FONACIDE")),
        ("other", _("Otro")),
    ]

    name = models.CharField(_("Nombre"), max_length=100, unique=True)
    code = models.CharField(_("Código"), max_length=20, unique=True)
    retention_type = models.CharField(
        _("Tipo de retención"), max_length=20, choices=RETENTION_TYPES, default="other"
    )
    percentage = models.DecimalField(
        _("Porcentaje"),
        max_digits=5,
        decimal_places=2,
        help_text=_("Porcentaje de retención (ej: 12.00 para 12%)"),
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    description = models.TextField(_("Descripción"), blank=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Tipo de Retención")
        verbose_name_plural = _("Tipos de Retención")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

    def clean(self):
        super().clean()
        if self.percentage < 0 or self.percentage > 100:
            raise ValidationError(_("El porcentaje debe estar entre 0 y 100."))


class PolicyRetention(models.Model):
    """
    Retentions applied to specific policies
    """

    policy = models.ForeignKey(
        "policies.Policy",
        on_delete=models.CASCADE,
        verbose_name=_("Póliza"),
        related_name="retentions",
    )
    retention_type = models.ForeignKey(
        RetentionType, on_delete=models.CASCADE, verbose_name=_("Tipo de retención")
    )
    applies_to_premium = models.BooleanField(
        _("Aplica a prima"),
        default=True,
        help_text=_("Si la retención se aplica sobre la prima"),
    )
    applies_to_total = models.BooleanField(
        _("Aplica a total"),
        default=False,
        help_text=_("Si la retención se aplica sobre el total de la factura"),
    )
    custom_percentage = models.DecimalField(
        _("Porcentaje personalizado"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Si es diferente al porcentaje estándar (opcional)"),
    )
    is_active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    created_by = models.ForeignKey(
        "accounts.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Creado por"),
    )

    class Meta:
        verbose_name = _("Retención de Póliza")
        verbose_name_plural = _("Retenciones de Póliza")
        unique_together = ["policy", "retention_type"]

    def __str__(self):
        return f"{self.policy} - {self.retention_type}"

    @property
    def effective_percentage(self):
        """Get the effective percentage (custom or default)"""
        return self.custom_percentage or self.retention_type.percentage

    def clean(self):
        super().clean()
        if not self.applies_to_premium and not self.applies_to_total:
            raise ValidationError(_("Debe aplicar al menos a la prima o al total."))
        if self.custom_percentage and (
            self.custom_percentage < 0 or self.custom_percentage > 100
        ):
            raise ValidationError(
                _("El porcentaje personalizado debe estar entre 0 y 100.")
            )
