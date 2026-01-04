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

    # Financial
    insured_value = models.DecimalField(
        _('Valor asegurado'),
        max_digits=15,
        decimal_places=2
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

    def clean(self):
        """
        Validate policy data
        """
        super().clean()

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

        self.full_clean()
        super().save(*args, **kwargs)


class PolicyDocument(models.Model):
    """
    Model for policy documents (policies, endorsements, certificates, etc.)
    """

    # Document type choices
    DOCUMENT_TYPE_CHOICES = [
        ('policy', _('Póliza')),
        ('endorsement', _('Endoso')),
        ('certificate', _('Certificado')),
        ('receipt', _('Recibo')),
        ('other', _('Otro')),
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
    file = models.FileField(
        _('Archivo'),
        upload_to='policies/documents/%Y/%m/'
    )
    file_size = models.PositiveIntegerField(
        _('Tamaño del archivo'),
        editable=False
    )
    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        verbose_name=_('Subido por'),
        related_name='uploaded_policy_documents'
    )
    uploaded_at = models.DateTimeField(_('Fecha de subida'), auto_now_add=True)

    class Meta:
        verbose_name = _('Documento de Póliza')
        verbose_name_plural = _('Documentos de Póliza')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document_name} ({self.policy.policy_number})"

    def save(self, *args, **kwargs):
        """
        Override save to calculate file size
        """
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete to remove file from storage
        """
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)
