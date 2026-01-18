from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Report
from accounts.models import UserProfile

class ReportForm(forms.ModelForm):
    """
    Form for creating and editing reports
    """

    class Meta:
        model = Report
        fields = [
            'name', 'report_type', 'description',
            'is_scheduled', 'schedule_frequency', 'recipients'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'recipients': forms.SelectMultiple(attrs={'size': 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields['name'].label = _('Nombre del Reporte')
        self.fields['report_type'].label = _('Tipo de Reporte')
        self.fields['description'].label = _('Descripción')
        self.fields['is_scheduled'].label = _('¿Programar reporte?')
        self.fields['schedule_frequency'].label = _('Frecuencia de envío')
        self.fields['recipients'].label = _('Destinatarios')

        # Set created_by automatically
        if self.user and not self.instance.pk:
            self.instance.created_by = self.user

    def clean(self):
        cleaned_data = super().clean()
        is_scheduled = cleaned_data.get('is_scheduled')
        schedule_frequency = cleaned_data.get('schedule_frequency')
        recipients = cleaned_data.get('recipients')

        if is_scheduled:
            if not schedule_frequency:
                raise forms.ValidationError(_('Debe especificar la frecuencia para reportes programados'))

            if not recipients:
                raise forms.ValidationError(_('Debe seleccionar al menos un destinatario para reportes programados'))

        return cleaned_data


class ReportFilterForm(forms.Form):
    """
    Form for filtering and generating reports
    """
    report_type = forms.ChoiceField(
        choices=[('', _('Seleccionar tipo de reporte'))] + Report.REPORT_TYPES,
        label=_('Tipo de Reporte'),
        required=True
    )

    # Date filters
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

    # Common filters
    insurance_company = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Compañía de Seguros'),
        empty_label=_('Todas las compañías')
    )
    broker = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Corredor'),
        empty_label=_('Todos los corredores')
    )
    responsible_user = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_('Usuario Responsable'),
        empty_label=_('Todos los usuarios')
    )

    # Specific filters for different report types
    days_ahead = forms.IntegerField(
        required=False,
        label=_('Días por delante'),
        help_text=_('Para reportes de vencimiento'),
        initial=30,
        min_value=1,
        max_value=365
    )

    status_filter = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('active', _('Activas')),
            ('expired', _('Vencidas')),
            ('cancelled', _('Canceladas')),
            ('renewed', _('Renovadas')),
        ],
        label=_('Estados'),
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Seleccionar múltiples estados')
    )

    claim_status_filter = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('reported', _('Reportado')),
            ('documentation_pending', _('Documentación pendiente')),
            ('sent_to_insurer', _('Enviado a aseguradora')),
            ('under_evaluation', _('En evaluación')),
            ('liquidated', _('Liquidado')),
            ('paid', _('Pagado')),
            ('closed', _('Cerrado')),
            ('rejected', _('Rechazado')),
        ],
        label=_('Estados de Siniestros'),
        widget=forms.CheckboxSelectMultiple,
        help_text=_('Seleccionar múltiples estados')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from companies.models import InsuranceCompany
        from brokers.models import Broker

        self.fields['insurance_company'].queryset = InsuranceCompany.objects.filter(is_active=True)
        self.fields['broker'].queryset = Broker.objects.filter(is_active=True)
        self.fields['responsible_user'].queryset = UserProfile.objects.filter(is_active=True)


class QuickReportForm(forms.Form):
    """
    Form for generating quick reports without saving
    """
    report_type = forms.ChoiceField(
        choices=Report.REPORT_TYPES,
        label=_('Tipo de Reporte'),
        required=True
    )
    export_format = forms.ChoiceField(
        choices=Report.EXPORT_FORMATS,
        label=_('Formato de Exportación'),
        initial='html'
    )

    # Quick filters
    date_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Seleccionar período')),
            ('today', _('Hoy')),
            ('yesterday', _('Ayer')),
            ('last_7_days', _('Últimos 7 días')),
            ('last_30_days', _('Últimos 30 días')),
            ('this_month', _('Este mes')),
            ('last_month', _('Mes anterior')),
            ('this_year', _('Este año')),
        ],
        label=_('Período'),
        help_text=_('Período predefinido para el reporte')
    )

    # Custom date range
    custom_date_from = forms.DateField(
        required=False,
        label=_('Fecha desde'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    custom_date_to = forms.DateField(
        required=False,
        label=_('Fecha hasta'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        custom_date_from = cleaned_data.get('custom_date_from')
        custom_date_to = cleaned_data.get('custom_date_to')

        if not date_range and not (custom_date_from and custom_date_to):
            raise forms.ValidationError(_('Debe seleccionar un período predefinido o especificar fechas personalizadas'))

        if custom_date_from and custom_date_to and custom_date_from > custom_date_to:
            raise forms.ValidationError(_('La fecha desde no puede ser posterior a la fecha hasta'))

        return cleaned_data


class ReportExecutionForm(forms.Form):
    """
    Form for executing saved reports
    """
    export_format = forms.ChoiceField(
        choices=Report.EXPORT_FORMATS,
        label=_('Formato de Exportación'),
        initial='html'
    )

    # Override filters
    override_filters = forms.BooleanField(
        required=False,
        label=_('¿Sobrescribir filtros del reporte?'),
        help_text=_('Si está marcado, puede cambiar los filtros del reporte guardado')
    )

    # Additional filters (shown when override_filters is True)
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




