from django import forms
from django.utils.translation import gettext_lazy as _

from .models import EmissionRights, InsuranceCompany, PolicyRetention, RetentionType


class InsuranceCompanyForm(forms.ModelForm):
    """
    Form for creating and editing insurance companies
    """

    class Meta:
        model = InsuranceCompany
        fields = [
            "name",
            "ruc",
            "address",
            "phone",
            "email",
            "contact_person",
            "is_active",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom labels and help texts
        self.fields["name"].label = _("Nombre de la Compañía")
        self.fields["ruc"].label = _("RUC")
        self.fields["ruc"].help_text = _(
            "Registro Único de Contribuyentes (13 dígitos)"
        )
        self.fields["address"].label = _("Dirección")
        self.fields["phone"].label = _("Teléfono")
        self.fields["email"].label = _("Email")
        self.fields["contact_person"].label = _("Persona de Contacto")
        self.fields["is_active"].label = _("Compañía Activa")

    def clean_ruc(self):
        """Validate RUC format"""
        ruc = self.cleaned_data.get("ruc")
        if ruc:
            # Remove any non-numeric characters
            ruc = "".join(filter(str.isdigit, ruc))

            # Check length
            if len(ruc) != 13:
                raise forms.ValidationError(
                    _("El RUC debe tener exactamente 13 dígitos")
                )

            # Basic Ecuadorian RUC validation (simplified)
            # First two digits should be valid province codes (01-24)
            if not (1 <= int(ruc[:2]) <= 24):
                raise forms.ValidationError(
                    _(
                        "Los primeros dos dígitos del RUC deben corresponder a una provincia válida (01-24)"
                    )
                )

        return ruc


class InsuranceCompanySearchForm(forms.Form):
    """
    Form for searching and filtering insurance companies
    """

    search = forms.CharField(
        required=False,
        label=_("Buscar"),
        widget=forms.TextInput(attrs={"placeholder": _("Nombre, RUC, contacto...")}),
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ("", _("Todos")),
            ("active", _("Activas")),
            ("inactive", _("Inactivas")),
        ],
        label=_("Estado"),
    )


class EmissionRightsForm(forms.ModelForm):
    """
    Form for creating and editing emission rights
    """

    class Meta:
        model = EmissionRights
        fields = [
            "min_amount",
            "max_amount",
            "emission_right",
            "is_active",
            "valid_from",
            "valid_until",
        ]
        widgets = {
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "min_amount": forms.NumberInput(attrs={"step": "0.01"}),
            "max_amount": forms.NumberInput(attrs={"step": "0.01"}),
            "emission_right": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields["min_amount"].label = _("Monto Mínimo")
        self.fields["max_amount"].label = _("Monto Máximo")
        self.fields["emission_right"].label = _("Derecho de Emisión")
        self.fields["is_active"].label = _("Activo")
        self.fields["valid_from"].label = _("Válido Desde")
        self.fields["valid_until"].label = _("Válido Hasta")

        # Set created_by automatically
        if self.user and not self.instance.pk:
            self.instance.created_by = self.user

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get("min_amount")
        max_amount = cleaned_data.get("max_amount")
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        # Validate amounts
        if min_amount and max_amount and min_amount >= max_amount:
            raise forms.ValidationError(
                _("El monto mínimo debe ser menor al monto máximo")
            )

        # Validate dates
        if valid_until and valid_from and valid_from >= valid_until:
            raise forms.ValidationError(
                _("La fecha de inicio debe ser anterior a la fecha de fin")
            )

        return cleaned_data


class RetentionTypeForm(forms.ModelForm):
    """
    Form for creating and editing retention types
    """

    class Meta:
        model = RetentionType
        fields = [
            "name",
            "code",
            "retention_type",
            "percentage",
            "is_active",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "percentage": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields["name"].label = _("Nombre del Tipo de Retención")
        self.fields["code"].label = _("Código")
        self.fields["retention_type"].label = _("Tipo de Retención")
        self.fields["percentage"].label = _("Porcentaje")
        self.fields["is_active"].label = _("Activo")
        self.fields["description"].label = _("Descripción")

    def clean_percentage(self):
        percentage = self.cleaned_data.get("percentage")
        if percentage is not None and (percentage < 0 or percentage > 100):
            raise forms.ValidationError(_("El porcentaje debe estar entre 0 y 100"))
        return percentage


class PolicyRetentionForm(forms.ModelForm):
    """
    Form for creating and editing policy retentions
    """

    class Meta:
        model = PolicyRetention
        fields = [
            "policy",
            "retention_type",
            "applies_to_premium",
            "applies_to_total",
            "custom_percentage",
            "is_active",
        ]
        widgets = {
            "custom_percentage": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields["policy"].label = _("Póliza")
        self.fields["retention_type"].label = _("Tipo de Retención")
        self.fields["applies_to_premium"].label = _("Aplica a Prima")
        self.fields["applies_to_total"].label = _("Aplica a Total de Factura")
        self.fields["custom_percentage"].label = _("Porcentaje Personalizado")
        self.fields["custom_percentage"].help_text = _(
            "Opcional. Si no se especifica, se usa el porcentaje estándar del tipo de retención."
        )
        self.fields["is_active"].label = _("Activo")

        # Set created_by automatically
        if self.user and not self.instance.pk:
            self.instance.created_by = self.user

    def clean(self):
        cleaned_data = super().clean()
        applies_to_premium = cleaned_data.get("applies_to_premium")
        applies_to_total = cleaned_data.get("applies_to_total")
        custom_percentage = cleaned_data.get("custom_percentage")

        # At least one application must be selected
        if not applies_to_premium and not applies_to_total:
            raise forms.ValidationError(
                _("La retención debe aplicar al menos a la prima o al total")
            )

        # Validate custom percentage
        if custom_percentage is not None and (
            custom_percentage < 0 or custom_percentage > 100
        ):
            raise forms.ValidationError(
                _("El porcentaje personalizado debe estar entre 0 y 100")
            )

        return cleaned_data
