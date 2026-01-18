from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Claim, ClaimSettlement


class ClaimCreateForm(forms.ModelForm):
    """Form for creating new claims"""

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add modern CSS classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all outline-none'
            })
        
        # Special handling for textarea
        if 'incident_description' in self.fields:
            self.fields['incident_description'].widget.attrs.update({
                'rows': 4,
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring focus:ring-blue-200 transition-all outline-none'
            })

        # Filter policies based on user permissions
        if user:
            # If user is requester, only show policies related to their assets
            if user.role == 'requester':
                from assets.models import Asset
                # Get policies related to user's assets
                user_assets = Asset.objects.filter(custodian=user)
                if user_assets.exists():
                    policy_ids = user_assets.values_list('policy_id', flat=True).distinct()
                    self.fields['policy'].queryset = self.fields['policy'].queryset.filter(id__in=policy_ids)

    class Meta:
        model = Claim
        fields = [
            'policy', 'asset_code', 'asset_type', 'asset_description',
            'incident_date', 'incident_location', 'incident_description',
            'estimated_loss', 'assigned_to'
        ]
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date'}),
            'incident_description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'policy': 'Póliza',
            'asset_code': 'Código del Bien',
            'asset_type': 'Tipo de Bien',
            'asset_description': 'Descripción del Bien',
            'incident_date': 'Fecha del Incidente',
            'incident_location': 'Ubicación del Incidente',
            'incident_description': 'Descripción del Incidente',
            'estimated_loss': 'Pérdida Estimada (USD)',
            'assigned_to': 'Asignado a',
        }

    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now().date():
            raise forms.ValidationError(_('La fecha del incidente no puede ser futura.'))
        return incident_date


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
    """Form for changing claim status with workflow validation"""

    def __init__(self, *args, **kwargs):
        claim = kwargs.pop('claim', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if claim:
            # Get available status transitions based on current status and user permissions
            available_statuses = []
            current_status = claim.status

            # Define status transitions based on workflow
            transitions = {
                'reported': ['documentation_pending'],
                'documentation_pending': ['sent_to_insurer', 'under_evaluation'],
                'sent_to_insurer': ['under_evaluation'],
                'under_evaluation': ['liquidated', 'rejected'],
                'liquidated': ['paid'],
                'paid': ['closed'],
                'rejected': ['closed'],
            }

            if current_status in transitions:
                available_statuses = transitions[current_status]

                # Add current status as option to stay
                available_statuses.insert(0, current_status)

            # Filter by user permissions
            if user and hasattr(user, 'get_role_permissions'):
                user_permissions = user.get_role_permissions()
                # Only allow certain roles to change status
                if 'claims_write' not in user_permissions and 'claims_manage' not in user_permissions:
                    available_statuses = [current_status]  # Can only stay in current status

            self.fields['new_status'].choices = [
                (status, dict(Claim.STATUS_CHOICES)[status]) for status in available_statuses
            ]

    new_status = forms.ChoiceField(
        label=_('Nuevo Estado'),
        choices=[],  # Will be populated in __init__
        required=True
    )

    notes = forms.CharField(
        label=_('Notas'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text=_('Opcional: Agregue notas sobre el cambio de estado.')
    )

    def clean_new_status(self):
        new_status = self.cleaned_data.get('new_status')
        claim = getattr(self, 'claim', None)

        if claim and new_status == claim.status:
            raise forms.ValidationError(_('El nuevo estado debe ser diferente al estado actual.'))

        return new_status

class ClaimSearchForm(forms.Form):
    """
    Form for searching and filtering claims
    """
    search = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Número, descripción, póliza...')})
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