from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from policies.models import Policy
from accounts.models import UserProfile
from companies.models import EmissionRights

class Invoice(models.Model):
    """
    Model for insurance invoices with automatic calculations
    """

    # Payment status choices
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pendiente')),
        ('paid', _('Pagada')),
        ('overdue', _('Vencida')),
        ('cancelled', _('Cancelada')),
    ]

    # Invoice fields
    policy = models.ForeignKey(
        Policy,
        on_delete=models.PROTECT,
        verbose_name=_('Póliza'),
        related_name='invoices'
    )
    invoice_number = models.CharField(
        _('Número de factura'),
        max_length=50,
        unique=True
    )
    invoice_date = models.DateField(_('Fecha de factura'))
    due_date = models.DateField(_('Fecha de vencimiento'))

    # Calculated fields (automatically computed)
    premium = models.DecimalField(
        _('Prima base'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    superintendence_contribution = models.DecimalField(
        _('Contribución Superintendencia (3.5%)'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    farm_insurance_contribution = models.DecimalField(
        _('Contribución Seguro Campesino (0.5%)'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    emission_rights = models.DecimalField(
        _('Derechos de emisión'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    tax_base = models.DecimalField(
        _('Base imponible'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    iva = models.DecimalField(
        _('IVA (15%)'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    withholding_tax = models.DecimalField(
        _('Retenciones'),
        max_digits=15,
        decimal_places=2,
        default=0,
        blank=True
    )
    early_payment_discount = models.DecimalField(
        _('Descuento pronto pago (5%)'),
        max_digits=15,
        decimal_places=2,
        editable=False,
        default=0
    )
    total_amount = models.DecimalField(
        _('Total final'),
        max_digits=15,
        decimal_places=2,
        editable=False
    )

    # Payment information
    payment_status = models.CharField(
        _('Estado de pago'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_date = models.DateField(
        _('Fecha de pago'),
        null=True,
        blank=True
    )

    # Relations
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Creado por'),
        related_name='created_invoices'
    )

    # Timestamps
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Factura')
        verbose_name_plural = _('Facturas')
        ordering = ['-created_at']

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.policy.policy_number}"

    def calculate_amounts(self):
        """
        Calculate all invoice amounts automatically
        """
        # 1. Prima base (se calcula basado en la póliza - por ahora usamos valor asegurado * 0.01)
        # En un sistema real, esto vendría de una tabla de tarifas
        self.premium = self.policy.insured_value * Decimal('0.01')  # 1% del valor asegurado

        # 2. Contribución Superintendencia (3.5% de prima)
        self.superintendence_contribution = self.premium * Decimal('0.035')

        # 3. Contribución Seguro Campesino (0.5% de prima)
        self.farm_insurance_contribution = self.premium * Decimal('0.005')

        # 4. Derechos de emisión (desde tabla configurable)
        self.emission_rights = EmissionRights.get_emission_right(self.premium)

        # 5. Base imponible = prima + superintendence + farm_insurance + emission_rights
        self.tax_base = (
            self.premium +
            self.superintendence_contribution +
            self.farm_insurance_contribution +
            self.emission_rights
        )

        # 6. IVA (15% sobre base imponible)
        self.iva = self.tax_base * Decimal('0.15')

        # 7. Descuento pronto pago (5% automático si pago ≤20 días)
        days_to_due = (self.due_date - self.invoice_date).days
        if days_to_due <= 20:
            self.early_payment_discount = self.tax_base * Decimal('0.05')
        else:
            self.early_payment_discount = 0

        # 8. Calcular retenciones de la póliza
        self.calculate_withholding_tax()

        # 9. Total final = base imponible + IVA - descuentos - retenciones
        self.total_amount = (
            self.tax_base +
            self.iva -
            self.early_payment_discount -
            self.withholding_tax
        )

    def calculate_withholding_tax(self):
        """
        Calculate withholding tax based on policy retentions
        """
        from companies.models import PolicyRetention

        # Get active retentions for this policy
        retentions = PolicyRetention.objects.filter(
            policy=self.policy,
            is_active=True
        )

        total_withholding = Decimal('0.00')

        for retention in retentions:
            if retention.applies_to_premium:
                # Apply retention to premium
                amount = self.premium * (retention.effective_percentage / 100)
                total_withholding += amount

            if retention.applies_to_total:
                # Apply retention to total amount before tax
                base_for_retention = (
                    self.premium +
                    self.superintendence_contribution +
                    self.farm_insurance_contribution +
                    self.emission_rights
                )
                amount = base_for_retention * (retention.effective_percentage / 100)
                total_withholding += amount

        self.withholding_tax = total_withholding

    def apply_early_payment_discount(self):
        """
        Apply early payment discount if payment is within 20 days
        """
        if self.payment_date and self.payment_status == 'paid':
            days_paid = (self.payment_date - self.invoice_date).days
            if days_paid <= 20 and self.early_payment_discount == 0:
                self.early_payment_discount = self.tax_base * Decimal('0.05')
                self.calculate_amounts()  # Recalculate total
                self.save()

    def clean(self):
        """
        Validate invoice data
        """
        super().clean()

        # Validate dates
        if self.due_date and self.invoice_date and self.due_date <= self.invoice_date:
            raise ValidationError(_('La fecha de vencimiento debe ser posterior a la fecha de factura'))

        # Validate payment date
        if self.payment_date and self.payment_status == 'paid' and self.payment_date < self.invoice_date:
            raise ValidationError(_('La fecha de pago no puede ser anterior a la fecha de factura'))

    @staticmethod
    def generate_invoice_number():
        """
        Generate unique invoice number
        """
        current_year = timezone.now().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{current_year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            try:
                seq_num = int(last_invoice.invoice_number.split('-')[-1])
                new_seq_num = seq_num + 1
            except (ValueError, IndexError):
                new_seq_num = 1
        else:
            new_seq_num = 1

        return f'INV-{current_year}-{new_seq_num:06d}'

    def save(self, *args, **kwargs):
        """
        Override save to generate invoice number and calculate amounts
        """
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        # Calculate amounts before saving only if they are not already set
        if not self.premium or self.premium == 0:
            self.calculate_amounts()

        self.full_clean()
        super().save(*args, **kwargs)
