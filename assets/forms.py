from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import UserProfile
from policies.models import Policy

from .models import Asset


class AssetForm(forms.ModelForm):
    """
    Form for creating and editing assets
    """

    class Meta:
        model = Asset
        fields = [
            "asset_code",
            "name",
            "description",
            "asset_type",
            "brand",
            "model",
            "serial_number",
            "location",
            "acquisition_date",
            "acquisition_cost",
            "current_value",
            "condition_status",
            "custodian",
            "responsible_user",
            "is_insured",
            "insurance_policy",
        ]
        widgets = {
            "acquisition_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "acquisition_cost": forms.NumberInput(attrs={"step": "0.01"}),
            "current_value": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields["asset_code"].label = _("Código del Activo")
        self.fields["name"].label = _("Nombre del Bien")
        self.fields["description"].label = _("Descripción")
        self.fields["asset_type"].label = _("Tipo de Activo")
        self.fields["brand"].label = _("Marca")
        self.fields["model"].label = _("Modelo")
        self.fields["serial_number"].label = _("Número de Serie")
        self.fields["location"].label = _("Ubicación Física")
        self.fields["acquisition_date"].label = _("Fecha de Adquisición")
        self.fields["acquisition_cost"].label = _("Costo de Adquisición")
        self.fields["current_value"].label = _("Valor Actual")
        self.fields["condition_status"].label = _("Estado de Condición")
        self.fields["custodian"].label = _("Custodio")
        self.fields["responsible_user"].label = _("Usuario Responsable")
        self.fields["is_insured"].label = _("¿Está Asegurado?")
        self.fields["insurance_policy"].label = _("Póliza de Seguro")

        # Filter choices based on user permissions
        if self.user:
            # Only requesters can be custodians
            self.fields["custodian"].queryset = UserProfile.objects.filter(
                is_active=True, role="requester"
            )
            # Make custodian required and add help text
            self.fields["custodian"].required = True
            self.fields["custodian"].help_text = _(
                "Seleccione el custodio responsable del bien (requerido)"
            )

            # Limit insurance policies based on permissions
            if not self.user.has_role_permission("policies_read"):
                # If user doesn't have general read permission, show only policies they're responsible for
                self.fields["insurance_policy"].queryset = Policy.objects.filter(
                    responsible_user=self.user, status="active"
                )
            else:
                self.fields["insurance_policy"].queryset = Policy.objects.filter(
                    status="active"
                )

    def clean(self):
        cleaned_data = super().clean()
        acquisition_date = cleaned_data.get("acquisition_date")
        acquisition_cost = cleaned_data.get("acquisition_cost")
        current_value = cleaned_data.get("current_value")
        is_insured = cleaned_data.get("is_insured")
        insurance_policy = cleaned_data.get("insurance_policy")

        # Validate dates
        if acquisition_date and acquisition_date > timezone.now().date():
            raise forms.ValidationError(
                _("La fecha de adquisición no puede ser futura")
            )

        # Validate costs
        if acquisition_cost and acquisition_cost <= 0:
            raise forms.ValidationError(
                _("El costo de adquisición debe ser mayor a cero")
            )

        if current_value and current_value < 0:
            raise forms.ValidationError(_("El valor actual no puede ser negativo"))

        if current_value and acquisition_cost and current_value > acquisition_cost:
            raise forms.ValidationError(
                _("El valor actual no puede ser mayor al costo de adquisición")
            )

        # Validate insurance
        if is_insured and not insurance_policy:
            raise forms.ValidationError(
                _("Debe seleccionar una póliza si el activo está asegurado")
            )

        if not is_insured and insurance_policy:
            # Clear insurance policy if not insured
            cleaned_data["insurance_policy"] = None

        return cleaned_data


class AssetSearchForm(forms.Form):
    """
    Form for searching and filtering assets
    """

    search = forms.CharField(
        required=False,
        label=_("Buscar"),
        widget=forms.TextInput(attrs={"placeholder": _("Código, nombre, marca...")}),
    )
    asset_type = forms.ChoiceField(
        required=False,
        choices=[("", _("Todos los tipos"))] + list(Asset.ASSET_TYPE_CHOICES),
        label=_("Tipo de Activo"),
    )
    condition_status = forms.ChoiceField(
        required=False,
        choices=[("", _("Todos los estados"))] + list(Asset.CONDITION_STATUS_CHOICES),
        label=_("Estado de Condición"),
    )
    is_insured = forms.ChoiceField(
        required=False,
        choices=[
            ("", _("Todos")),
            ("insured", _("Asegurados")),
            ("uninsured", _("No asegurados")),
        ],
        label=_("Estado de Seguro"),
    )
    custodian = forms.ModelChoiceField(
        required=False,
        queryset=UserProfile.objects.filter(is_active=True, role="requester"),
        label=_("Custodio"),
        empty_label=_("Todos los custodios"),
    )


class AssetCustodianChangeForm(forms.ModelForm):
    """
    Form for changing asset custodian
    """

    class Meta:
        model = Asset
        fields = ["custodian"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["custodian"].label = _("Nuevo Custodio")
        self.fields["custodian"].queryset = UserProfile.objects.filter(
            is_active=True, role="requester"
        )
        self.fields["custodian"].help_text = _(
            "Seleccione el nuevo custodio del activo"
        )

    def clean_custodian(self):
        custodian = self.cleaned_data.get("custodian")
        if custodian and custodian.role != "requester":
            raise forms.ValidationError(
                _('El custodio debe tener el rol de "Custodio de bienes"')
            )
        return custodian


from claims.models import Claim


class AssetClaimReportForm(forms.ModelForm):
    """
    Formulario simplificado para reportar siniestro desde un bien
    El bien ya está seleccionado, solo se necesita información del siniestro
    """

    initial_document = forms.FileField(
        required=False,
        label=_("Adjuntar Documento Inicial (PDF/Imagen)"),
        help_text=_("Opcional: Cargue un reporte inicial, fotos o denuncia."),
        # Widget attrs will be handled by default but can stay standard
    )

    class Meta:
        model = Claim
        fields = [
            "fecha_siniestro",
            "causa",
            "ubicacion_detallada",
            "incident_description",
            "estimated_loss",
        ]
        widgets = {
            "fecha_siniestro": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "causa": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Describa la causa del siniestro (ej: Robo, Daño por agua, Incendio, etc.)",
                }
            ),
            "ubicacion_detallada": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "form-control",
                    "placeholder": "Ubicación específica donde ocurrió el siniestro",
                }
            ),
            "incident_description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Descripción detallada de lo ocurrido",
                }
            ),
            "estimated_loss": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
            ),
        }
        labels = {
            "fecha_siniestro": _("Fecha del Siniestro"),
            "causa": _("Causa del Siniestro"),
            "ubicacion_detallada": _("Ubicación Detallada"),
            "incident_description": _("Descripción del Incidente"),
            "estimated_loss": _("Pérdida Estimada (USD)"),
        }

    def __init__(self, *args, **kwargs):
        self.asset = kwargs.pop("asset", None)
        super().__init__(*args, **kwargs)

        # Prellenar fecha con hoy
        if not self.instance.pk:
            self.fields["fecha_siniestro"].initial = timezone.now().date()

        # Prellenar ubicación con la del bien si está disponible
        if self.asset and not self.instance.pk:
            self.fields["ubicacion_detallada"].initial = self.asset.location

            # Agregar información del bien en help_text
            self.fields["incident_description"].help_text = _(
                f"Bien afectado: {self.asset.name} ({self.asset.asset_code})"
            )

    def clean_fecha_siniestro(self):
        fecha = self.cleaned_data.get("fecha_siniestro")
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError(_("La fecha del siniestro no puede ser futura"))
        return fecha

    def clean_estimated_loss(self):
        loss = self.cleaned_data.get("estimated_loss")
        if loss and loss < 0:
            raise forms.ValidationError(_("La pérdida estimada no puede ser negativa"))
        return loss
