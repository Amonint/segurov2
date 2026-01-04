from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Policy, PolicyDocument
from companies.models import InsuranceCompany
from brokers.models import Broker
from accounts.models import UserProfile

class PolicyForm(forms.ModelForm):
    """
    Form for creating and editing insurance policies
    """

    class Meta:
        model = Policy
        fields = [
            'policy_number', 'insurance_company', 'broker',
            'group_type', 'subgroup', 'branch',
            'start_date', 'end_date', 'issue_date',
            'insured_value', 'coverage_description', 'observations',
            'responsible_user'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'insured_value': forms.NumberInput(attrs={'step': '0.01'}),
            'coverage_description': forms.Textarea(attrs={'rows': 3}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make fields required as per business logic
        self.fields['insurance_company'].required = True
        self.fields['group_type'].required = True
        self.fields['subgroup'].required = True
        self.fields['branch'].required = True
        self.fields['start_date'].required = True
        self.fields['end_date'].required = True
        self.fields['insured_value'].required = True

        # Custom labels
        self.fields['policy_number'].label = _('Número de Póliza')
        self.fields['insurance_company'].label = _('Compañía de Seguros')
        self.fields['broker'].label = _('Corredor (Opcional)')
        self.fields['group_type'].label = _('Tipo de Grupo')
        self.fields['subgroup'].label = _('Subgrupo')
        self.fields['branch'].label = _('Rama')
        self.fields['start_date'].label = _('Fecha de Inicio')
        self.fields['end_date'].label = _('Fecha de Fin')
        self.fields['issue_date'].label = _('Fecha de Emisión')
        self.fields['insured_value'].label = _('Valor Asegurado')
        self.fields['coverage_description'].label = _('Descripción de Cobertura')
        self.fields['observations'].label = _('Observaciones')
        self.fields['responsible_user'].label = _('Usuario Responsable')

        # Limit choices for responsible user to active users with appropriate roles
        self.fields['responsible_user'].queryset = UserProfile.objects.filter(
            is_active=True,
            role__in=['admin', 'insurance_manager']
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        issue_date = cleaned_data.get('issue_date')
        insured_value = cleaned_data.get('insured_value')

        # Validate dates
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio'))

        if issue_date and start_date and issue_date > start_date:
            raise forms.ValidationError(_('La fecha de emisión no puede ser posterior a la fecha de inicio'))

        # Validate insured value
        if insured_value and insured_value <= 0:
            raise forms.ValidationError(_('El valor asegurado debe ser mayor a cero'))

        return cleaned_data


class PolicySearchForm(forms.Form):
    """
    Form for searching and filtering policies
    """
    search = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Número de póliza, compañía...')})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('Todos los estados'))] + list(Policy.STATUS_CHOICES),
        label=_('Estado')
    )
    group_type = forms.ChoiceField(
        required=False,
        choices=[('', _('Todos los grupos'))] + list(Policy.GROUP_TYPE_CHOICES),
        label=_('Tipo de Grupo')
    )
    insurance_company = forms.ModelChoiceField(
        required=False,
        queryset=InsuranceCompany.objects.all(),
        label=_('Compañía de Seguros'),
        empty_label=_('Todas las compañías')
    )
    broker = forms.ModelChoiceField(
        required=False,
        queryset=Broker.objects.all(),
        label=_('Corredor'),
        empty_label=_('Todos los corredores')
    )
    responsible_user = forms.ModelChoiceField(
        required=False,
        queryset=UserProfile.objects.filter(is_active=True),
        label=_('Usuario Responsable'),
        empty_label=_('Todos los usuarios')
    )
    expiring_soon = forms.BooleanField(
        required=False,
        label=_('Por vencer (30 días)'),
        help_text=_('Mostrar solo pólizas que vencen en los próximos 30 días')
    )


class PolicyRenewalForm(forms.ModelForm):
    """
    Form for renewing policies
    """
    new_end_date = forms.DateField(
        label=_('Nueva Fecha de Fin'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_('Fecha de finalización de la póliza renovada')
    )

    class Meta:
        model = Policy
        fields = ['observations']

    def __init__(self, *args, **kwargs):
        self.current_policy = kwargs.pop('current_policy', None)
        super().__init__(*args, **kwargs)

    def clean_new_end_date(self):
        new_end_date = self.cleaned_data['new_end_date']
        if self.current_policy and new_end_date <= self.current_policy.end_date:
            raise forms.ValidationError(_('La nueva fecha de fin debe ser posterior a la fecha actual'))
        return new_end_date


class PolicyDocumentForm(forms.ModelForm):
    """
    Form for uploading policy documents
    """

    class Meta:
        model = PolicyDocument
        fields = ['document_name', 'document_type', 'file', 'description', 'tags']
        widgets = {
            'document_name': forms.TextInput(attrs={'placeholder': _('Nombre descriptivo del documento')}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Descripción opcional del documento')}),
            'tags': forms.TextInput(attrs={'placeholder': _('Etiquetas separadas por comas')}),
        }

    def __init__(self, *args, **kwargs):
        self.policy = kwargs.pop('policy', None)
        self.uploaded_by = kwargs.pop('uploaded_by', None)
        super().__init__(*args, **kwargs)

        # Set dynamic choices based on policy
        if self.policy:
            self.fields['document_type'].choices = PolicyDocument.get_document_types_for_policy(self.policy)

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError(_('El archivo no puede ser mayor a 10MB.'))

            # Check file type
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'image/jpeg',
                'image/png',
                'image/gif',
                'text/plain'
            ]

            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise forms.ValidationError(_('Tipo de archivo no permitido. Solo se permiten PDFs, documentos Word, Excel, imágenes y archivos de texto.'))

        return file

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.policy = self.policy
        instance.uploaded_by = self.uploaded_by
        if commit:
            instance.save()
        return instance


class PolicyDocumentEditForm(forms.ModelForm):
    """
    Form for editing policy document metadata
    """

    class Meta:
        model = PolicyDocument
        fields = ['document_name', 'document_type', 'description', 'tags']
        widgets = {
            'document_name': forms.TextInput(attrs={'placeholder': _('Nombre descriptivo del documento')}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Descripción opcional del documento')}),
            'tags': forms.TextInput(attrs={'placeholder': _('Etiquetas separadas por comas')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set dynamic choices based on policy
        if self.instance and self.instance.policy:
            self.fields['document_type'].choices = PolicyDocument.get_document_types_for_policy(self.instance.policy)
