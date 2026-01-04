from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Broker

class BrokerForm(forms.ModelForm):
    """
    Form for creating and editing brokers
    """

    class Meta:
        model = Broker
        fields = [
            'name', 'ruc', 'address', 'phone', 'email',
            'contact_person', 'commission_percentage', 'is_active'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'commission_percentage': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom labels and help texts
        self.fields['name'].label = _('Nombre del Corredor')
        self.fields['ruc'].label = _('RUC')
        self.fields['ruc'].help_text = _('Registro Único de Contribuyentes (13 dígitos)')
        self.fields['address'].label = _('Dirección')
        self.fields['phone'].label = _('Teléfono')
        self.fields['email'].label = _('Email')
        self.fields['contact_person'].label = _('Persona de Contacto')
        self.fields['commission_percentage'].label = _('Porcentaje de Comisión')
        self.fields['commission_percentage'].help_text = _('Porcentaje de comisión sobre las pólizas (0-100%)')
        self.fields['is_active'].label = _('Corredor Activo')

    def clean_ruc(self):
        """Validate RUC format"""
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            # Remove any non-numeric characters
            ruc = ''.join(filter(str.isdigit, ruc))

            # Check length
            if len(ruc) != 13:
                raise forms.ValidationError(_('El RUC debe tener exactamente 13 dígitos'))

            # Basic Ecuadorian RUC validation (simplified)
            # First two digits should be valid province codes (01-24)
            if not (1 <= int(ruc[:2]) <= 24):
                raise forms.ValidationError(_('Los primeros dos dígitos del RUC deben corresponder a una provincia válida (01-24)'))

        return ruc

    def clean_commission_percentage(self):
        """Validate commission percentage"""
        percentage = self.cleaned_data.get('commission_percentage')
        if percentage is not None and (percentage < 0 or percentage > 100):
            raise forms.ValidationError(_('El porcentaje de comisión debe estar entre 0 y 100'))
        return percentage


class BrokerSearchForm(forms.Form):
    """
    Form for searching and filtering brokers
    """
    search = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Nombre, RUC, contacto...')})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Todos')),
            ('active', _('Activos')),
            ('inactive', _('Inactivos'))
        ],
        label=_('Estado')
    )
    commission_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Todas las comisiones')),
            ('low', _('Baja (0-5%)')),
            ('medium', _('Media (5-15%)')),
            ('high', _('Alta (15%+)')),
        ],
        label=_('Rango de Comisión')
    )
