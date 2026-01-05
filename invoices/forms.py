from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Invoice
from policies.models import Policy
from accounts.models import UserProfile

class InvoiceForm(forms.ModelForm):
    """
    Form for creating and editing invoices
    """

    class Meta:
        model = Invoice
        fields = [
            'policy', 'invoice_date', 'due_date',
            'created_by'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter policies based on user permissions
        if self.user:
            # If user is not admin/manager, only show policies they're responsible for
            if not self.user.has_role_permission('invoices_write'):
                self.fields['policy'].queryset = Policy.objects.filter(
                    responsible_user=self.user
                )
            else:
                self.fields['policy'].queryset = Policy.objects.filter(
                    status__in=['active', 'expired']
                )

        # Set created_by automatically
        if self.user and not self.instance.pk:
            self.fields['created_by'].initial = self.user

        # Custom labels
        self.fields['policy'].label = _('Póliza')
        self.fields['invoice_date'].label = _('Fecha de Factura')
        self.fields['due_date'].label = _('Fecha de Vencimiento')
        self.fields['created_by'].label = _('Creado por')

    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        policy = cleaned_data.get('policy')

        # Validate dates
        if invoice_date and due_date and due_date <= invoice_date:
            raise forms.ValidationError(_('La fecha de vencimiento debe ser posterior a la fecha de factura'))

        # Validate policy
        if policy and policy.status not in ['active', 'expired']:
            raise forms.ValidationError(_('No se pueden crear facturas para pólizas canceladas o renovadas'))

        return cleaned_data


class InvoicePaymentForm(forms.ModelForm):
    """
    Form for recording invoice payments
    """

    class Meta:
        model = Invoice
        fields = ['payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_date'].label = _('Fecha de Pago')
        self.fields['payment_date'].required = True

    def clean_payment_date(self):
        payment_date = self.cleaned_data['payment_date']
        invoice_date = self.instance.invoice_date

        if payment_date < invoice_date:
            raise forms.ValidationError(_('La fecha de pago no puede ser anterior a la fecha de factura'))

        return payment_date


class InvoiceSearchForm(forms.Form):
    """
    Form for searching and filtering invoices
    """
    search = forms.CharField(
        required=False,
        label=_('Buscar'),
        widget=forms.TextInput(attrs={'placeholder': _('Número de factura, póliza...')})
    )
    payment_status = forms.ChoiceField(
        required=False,
        choices=[('', _('Todos los estados'))] + list(Invoice.PAYMENT_STATUS_CHOICES),
        label=_('Estado de Pago')
    )
    policy = forms.ModelChoiceField(
        required=False,
        queryset=Policy.objects.all(),
        label=_('Póliza'),
        empty_label=_('Todas las pólizas')
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
    created_by = forms.ModelChoiceField(
        required=False,
        queryset=UserProfile.objects.filter(is_active=True),
        label=_('Creado por'),
        empty_label=_('Todos los usuarios')
    )
    overdue = forms.BooleanField(
        required=False,
        label=_('Solo vencidas'),
        help_text=_('Mostrar solo facturas vencidas')
    )


class InvoiceBulkActionForm(forms.Form):
    """
    Form for bulk actions on invoices
    """
    action = forms.ChoiceField(
        choices=[
            ('', _('Seleccionar acción')),
            ('mark_paid', _('Marcar como pagadas')),
            ('export', _('Exportar')),
        ],
        label=_('Acción')
    )
    payment_date = forms.DateField(
        required=False,
        label=_('Fecha de Pago'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_('Fecha de pago para marcar como pagadas')
    )
    invoice_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        payment_date = cleaned_data.get('payment_date')

        if action == 'mark_paid' and not payment_date:
            raise forms.ValidationError(_('Debe especificar una fecha de pago'))

        return cleaned_data




