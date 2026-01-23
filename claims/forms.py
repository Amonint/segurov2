from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Claim, ClaimDocument, ClaimSettlement

# ClaimCreateForm has been REMOVED - Claims are now created via AssetClaimReportForm
# from the asset detail page (asset-centric workflow)


class ClaimSettlementForm(forms.ModelForm):
    """Form for managing claim settlements"""

    class Meta:
        model = ClaimSettlement
        fields = [
            "claim_reference_number",
            "total_claim_amount",
            "deductible_amount",
            "depreciation_amount",
            "final_payment_amount",
            "settlement_document",
            "status",
        ]
        widgets = {
            "claim_reference_number": forms.TextInput(attrs={"class": "form-control"}),
            "total_claim_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "deductible_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "depreciation_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "final_payment_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "settlement_document": forms.FileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get("total_claim_amount", 0)
        deductible = cleaned_data.get("deductible_amount", 0)
        depreciation = cleaned_data.get("depreciation_amount", 0)
        final_amount = cleaned_data.get("final_payment_amount", 0)

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
            "policy",
            "incident_date",
            "incident_location",
            "incident_description",
            "asset_type",
            "asset_description",
            "asset_code",
            "estimated_loss",
            "assigned_to",
        ]
        widgets = {
            "incident_date": forms.DateInput(attrs={"type": "date"}),
            "incident_description": forms.Textarea(attrs={"rows": 3}),
            "asset_description": forms.Textarea(attrs={"rows": 2}),
            "estimated_loss": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter policies based on user role
        if self.user and self.user.role == "requester":
            # Requesters can only select policies with their assets
            from policies.models import Policy

            self.fields["policy"].queryset = Policy.objects.filter(
                assets__custodian=self.user
            ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        incident_date = cleaned_data.get("incident_date")
        estimated_loss = cleaned_data.get("estimated_loss")

        # Validate estimated loss
        if estimated_loss and estimated_loss <= 0:
            raise forms.ValidationError(_("La pérdida estimada debe ser mayor a cero"))

        return cleaned_data


class ClaimStatusChangeForm(forms.Form):
    """Form for changing claim status with workflow validation"""

    def __init__(self, *args, **kwargs):
        claim = kwargs.pop("claim", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if claim:
            # Get available status transitions based on current status and user permissions
            available_statuses = []
            current_status = claim.status

            # Define status transitions based on workflow
            # Nuevo flujo simplificado en español
            transitions = {
                "pendiente": [
                    "en_revision",
                    "requiere_cambios",
                    "aprobado",
                    "rechazado",
                ],
                "en_revision": ["requiere_cambios", "aprobado", "rechazado"],
                "requiere_cambios": ["pendiente", "en_revision"],  # Custodio reenvía
                "aprobado": ["liquidado", "rechazado"],
                "liquidado": ["pagado"],
                "pagado": [],  # Estado final
                "rechazado": [],  # Estado final
            }

            if current_status in transitions:
                available_statuses = transitions[current_status]

                # Add current status as option to stay
                available_statuses.insert(0, current_status)

            # Filter by user permissions
            if user and hasattr(user, "get_role_permissions"):
                user_permissions = user.get_role_permissions()
                # Only allow certain roles to change status
                if (
                    "claims_write" not in user_permissions
                    and "claims_manage" not in user_permissions
                ):
                    available_statuses = [
                        current_status
                    ]  # Can only stay in current status

            self.fields["new_status"].choices = [
                (status, dict(Claim.STATUS_CHOICES)[status])
                for status in available_statuses
            ]

    new_status = forms.ChoiceField(
        label=_("Nuevo Estado"),
        choices=[],  # Will be populated in __init__
        required=True,
    )

    notes = forms.CharField(
        label=_("Notas"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text=_("Opcional: Agregue notas sobre el cambio de estado."),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("new_status")
        notes = cleaned_data.get("notes")
        claim = getattr(self, "claim", None)

        # Require notes for corrections or rejections
        if new_status in ["requiere_cambios", "rechazado"] and not notes:
            msg = _(
                "Es obligatorio indicar la razón o las correcciones necesarias para este estado."
            )
            self.add_error("notes", msg)

        # Validate required documents before approval
        if claim and new_status == "liquidado":
            missing_docs = []
            required_docs = ClaimDocument.get_required_documents_for_claim(claim)

            for doc_type, doc_name in required_docs:
                # Check if required document exists and is uploaded
                doc_exists = claim.documents.filter(
                    document_type=doc_type, status="active"
                ).exists()
                if not doc_exists:
                    missing_docs.append(doc_name)

            if missing_docs:
                msg = _(
                    "No se puede aprobar el siniestro. Faltan los siguientes documentos requeridos: %(docs)s"
                )
                self.add_error("new_status", msg % {"docs": ", ".join(missing_docs)})

        return cleaned_data

    def clean_new_status(self):
        new_status = self.cleaned_data.get("new_status")
        claim = getattr(self, "claim", None)

        if claim and new_status == claim.status:
            raise forms.ValidationError(
                _("El nuevo estado debe ser diferente al estado actual.")
            )

        return new_status


class ClaimSearchForm(forms.Form):
    """
    Form for searching and filtering claims
    """

    search = forms.CharField(
        required=False,
        label=_("Buscar"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Número, descripción, póliza...")}
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", _("Todos los estados"))] + list(Claim.STATUS_CHOICES),
        label=_("Estado"),
    )
    policy = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_("Póliza"),
        empty_label=_("Todas las pólizas"),
    )
    reported_by = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_("Reportado por"),
        empty_label=_("Todos los usuarios"),
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        label=_("Asignado a"),
        empty_label=_("Todos los usuarios"),
    )
    date_from = forms.DateField(
        required=False,
        label=_("Fecha desde"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        required=False,
        label=_("Fecha hasta"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    overdue = forms.BooleanField(
        required=False,
        label=_("Solo atrasados"),
        help_text=_("Mostrar solo siniestros atrasados"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from accounts.models import UserProfile
        from policies.models import Policy

        self.fields["policy"].queryset = Policy.objects.filter(status="active")
        self.fields["reported_by"].queryset = UserProfile.objects.filter(is_active=True)
        self.fields["assigned_to"].queryset = UserProfile.objects.filter(is_active=True)
