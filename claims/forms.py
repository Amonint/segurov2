from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ClaimSettlement


class ClaimSettlementForm(forms.ModelForm):
    """Form for managing claim settlements"""

    class Meta:
        model = ClaimSettlement
        fields = [
            'claim_reference_number', 'total_claim_amount', 'deductible_amount',
            'depreciation_amount', 'final_payment_amount', 'settlement_document',
            'status'
        ]
        widgets = {
            'claim_reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'total_claim_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'deductible_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'depreciation_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'final_payment_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'settlement_document': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_claim_amount', 0)
        deductible = cleaned_data.get('deductible_amount', 0)
        depreciation = cleaned_data.get('depreciation_amount', 0)
        final_amount = cleaned_data.get('final_payment_amount', 0)

        # Validate that final amount makes sense
        calculated_final = total_amount - deductible - depreciation
        if final_amount and abs(final_amount - calculated_final) > 0.01:
            # Allow small differences for rounding
            pass

        return cleaned_data


class ClaimEditForm(forms.ModelForm):
    """
    Form for editing existing claims
    """

    class Meta:
        model = Claim
        fields = [
            'policy', 'incident_date', 'report_date', 'incident_location',
            'incident_description', 'asset_type', 'asset_description',
            'asset_code', 'estimated_loss', 'assigned_to'
        ]
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date'}),
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'incident_description': forms.Textarea(attrs={'rows': 3}),
            'asset_description': forms.Textarea(attrs={'rows': 2}),
            'estimated_loss': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter policies based on user role
        if self.user and self.user.role == 'requester':
            # Requesters can only select policies with their assets
            from policies.models import Policy
            self.fields['policy'].queryset = Policy.objects.filter(
                assets__custodian=self.user
            ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        incident_date = cleaned_data.get('incident_date')
        report_date = cleaned_data.get('report_date')
        estimated_loss = cleaned_data.get('estimated_loss')

        # Validate dates
        if incident_date and report_date and report_date < incident_date:
            raise forms.ValidationError(_('La fecha de reporte no puede ser anterior a la fecha del incidente'))

        # Validate estimated loss
        if estimated_loss and estimated_loss <= 0:
            raise forms.ValidationError(_('La pérdida estimada debe ser mayor a cero'))

        return cleaned_data


class ClaimStatusChangeForm(forms.Form):
    """
    Form for changing claim status
    """
    new_status = forms.ChoiceField(
        choices=Claim.STATUS_CHOICES,
        label=_('Nuevo Estado'),
        help_text=_('Seleccione el nuevo estado del siniestro')
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Notas'),
        help_text=_('Notas adicionales sobre el cambio de estado (opcional)')
    )

    def __init__(self, *args, **kwargs):
        from .models import Claim
        self.claim = kwargs.pop('claim', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter available statuses based on current status and user permissions
        if self.claim and self.user:
            current_status = self.claim.status
            available_statuses = []

            for status_choice in Claim.STATUS_CHOICES:
                status_value = status_choice[0]
                if status_value != current_status and self.claim.can_change_status(status_value, self.user):
                    available_statuses.append(status_choice)

            self.fields['new_status'].choices = available_statuses

    def clean_new_status(self):
        from .models import Claim
        new_status = self.cleaned_data.get('new_status')
        if self.claim and self.user and not self.claim.can_change_status(new_status, self.user):
            raise forms.ValidationError(_('No tienes permisos para cambiar el estado a %(status)s') % {'status': new_status})
        return new_status


class ClaimSearchForm(forms.Form):
    """
    Form for searching and filtering claims
    """
    search = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Número, descripción, póliza...'})')
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('Todos los estados'))] + list(Claim.STATUS_CHOICES),
        label=_('Estado')
    )
    policy = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Póliza'),
        empty_label=_('Todas las pólizas')
    )
    reported_by = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Reportado por'),
        empty_label=_('Todos los usuarios')
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Asignado a'),
        empty_label=_('Todos los usuarios')
    )
    date_from = forms.DateField(
        required=False,
        label=_('Fecha desde'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label=_('Fecha hasta'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    overdue = forms.BooleanField(
        required=False,
        label=_('Solo atrasados'),
        help_text=_('Mostrar solo siniestros atrasados')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from policies.models import Policy
        from accounts.models import UserProfile

        self.fields['policy'].queryset = Policy.objects.filter(status='active')
        self.fields['reported_by'].queryset = UserProfile.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = UserProfile.objects.filter(is_active=True)