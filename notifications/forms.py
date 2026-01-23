from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Alert, EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    """Form for managing email templates"""

    class Meta:
        model = EmailTemplate
        fields = [
            "name",
            "template_type",
            "recipient_type",
            "subject",
            "body_html",
            "body_text",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "template_type": forms.Select(attrs={"class": "form-control"}),
            "recipient_type": forms.Select(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body_html": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 15,
                    "placeholder": "Cuerpo del email en HTML. Puede usar variables como {{claim_number}}, {{user_name}}, etc.",
                }
            ),
            "body_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Versión texto plano del email (opcional)",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_body_html(self):
        """Validate HTML content"""
        body_html = self.cleaned_data.get("body_html")
        if body_html and len(body_html.strip()) < 10:
            raise forms.ValidationError(
                _("El cuerpo HTML debe tener al menos 10 caracteres.")
            )
        return body_html

    def clean_subject(self):
        """Validate subject contains variables if needed"""
        subject = self.cleaned_data.get("subject")
        if subject and "{{" in subject and "}}" not in subject:
            raise forms.ValidationError(
                _(
                    "Las variables en el asunto deben estar completas (ej: {{variable}})."
                )
            )
        return subject


class AlertForm(forms.ModelForm):
    """
    Form for creating and editing alerts
    """

    class Meta:
        model = Alert
        fields = [
            "name",
            "alert_type",
            "description",
            "conditions",
            "recipients",
            "email_recipients",
            "frequency",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "conditions": forms.Textarea(
                attrs={"rows": 5, "placeholder": 'Ejemplo: {"days_ahead": 30}'}
            ),
            "email_recipients": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "email1@example.com, email2@example.com",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom labels
        self.fields["name"].label = _("Nombre de la Alerta")
        self.fields["alert_type"].label = _("Tipo de Alerta")
        self.fields["description"].label = _("Descripción")
        self.fields["conditions"].label = _("Condiciones (JSON)")
        self.fields["recipients"].label = _("Destinatarios")
        self.fields["email_recipients"].label = _("Emails Adicionales")
        self.fields["frequency"].label = _("Frecuencia")
        self.fields["is_active"].label = _("Alerta Activa")

        # Help texts
        self.fields["conditions"].help_text = _(
            'Condiciones específicas en formato JSON. Ejemplo: {"days_ahead": 30} para alertas de vencimiento.'
        )
        self.fields["email_recipients"].help_text = _(
            "Direcciones de email adicionales separadas por comas."
        )

    def clean_conditions(self):
        """Validate JSON conditions"""
        import json

        conditions = self.cleaned_data.get("conditions", "{}")
        if isinstance(conditions, str):
            try:
                return json.loads(conditions)
            except json.JSONDecodeError:
                raise forms.ValidationError(
                    _("Las condiciones deben ser un JSON válido.")
                )
        return conditions

    def clean_email_recipients(self):
        """Validate email addresses"""
        from django.core.validators import validate_email

        emails = self.cleaned_data.get("email_recipients", "").strip()

        if emails:
            email_list = [email.strip() for email in emails.split(",") if email.strip()]
            for email in email_list:
                try:
                    validate_email(email)
                except:
                    raise forms.ValidationError(f"Email inválido: {email}")
            return ", ".join(email_list)

        return emails
