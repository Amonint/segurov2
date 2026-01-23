from django import forms
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


class UserProfileCreationForm(UserCreationForm):
    """
    Form for creating new users with role selection
    """

    full_name = forms.CharField(
        max_length=255,
        required=False,
        label=_("Nombre completo"),
        help_text=_("Nombre completo del usuario (opcional)"),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label=_("Rol"),
        help_text=_("Rol del usuario en el sistema"),
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        label=_("Departamento"),
        help_text=_("Departamento al que pertenece el usuario"),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_("Teléfono"),
        help_text=_("Número de teléfono del usuario"),
    )

    class Meta:
        model = UserProfile
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "department",
            "phone",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields["email"].required = True
        # Custom field order
        self.order_fields(
            [
                "username",
                "email",
                "first_name",
                "last_name",
                "full_name",
                "role",
                "department",
                "phone",
                "password1",
                "password2",
            ]
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data.get("full_name", "")
        user.role = self.cleaned_data["role"]
        user.department = self.cleaned_data.get("department", "")
        user.phone = self.cleaned_data.get("phone", "")

        if commit:
            user.save()
        return user


class UserProfileChangeForm(UserChangeForm):
    """
    Form for editing existing users
    """

    full_name = forms.CharField(
        max_length=255,
        required=False,
        label=_("Nombre completo"),
        help_text=_("Nombre completo del usuario (opcional)"),
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label=_("Rol"),
        help_text=_("Rol del usuario en el sistema"),
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        label=_("Departamento"),
        help_text=_("Departamento al que pertenece el usuario"),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_("Teléfono"),
        help_text=_("Número de teléfono del usuario"),
    )
    is_active = forms.BooleanField(
        required=False,
        label=_("Usuario activo"),
        help_text=_("Desmarcar para desactivar el usuario"),
    )

    class Meta:
        model = UserProfile
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "department",
            "phone",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password field (handled separately)
        if "password" in self.fields:
            del self.fields["password"]
        # Set initial values
        if self.instance:
            self.fields["full_name"].initial = self.instance.full_name
            self.fields["role"].initial = self.instance.role
            self.fields["department"].initial = self.instance.department
            self.fields["phone"].initial = self.instance.phone
            self.fields["is_active"].initial = self.instance.is_active


class UserProfilePasswordChangeForm(PasswordChangeForm):
    """
    Form for changing user password
    """

    class Meta:
        model = UserProfile
        fields = ("old_password", "new_password1", "new_password2")


class UserProfileSearchForm(forms.Form):
    """
    Form for searching and filtering users
    """

    search = forms.CharField(
        required=False,
        label=_("Buscar"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Buscar por nombre, usuario o email")}
        ),
    )
    role = forms.ChoiceField(
        required=False,
        choices=[("", _("Todos los roles"))] + list(UserProfile.ROLE_CHOICES),
        label=_("Rol"),
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ("", _("Todos")),
            ("active", _("Activos")),
            ("inactive", _("Inactivos")),
        ],
        label=_("Estado"),
    )
    department = forms.CharField(
        required=False,
        label=_("Departamento"),
        widget=forms.TextInput(attrs={"placeholder": _("Filtrar por departamento")}),
    )


class UserProfilePasswordResetForm(forms.Form):
    """
    Form for password reset request
    """

    email = forms.EmailField(
        label=_("Email"),
        help_text=_("Ingresa el email del usuario para enviar el enlace de reset"),
    )


class UserProfileSetPasswordForm(forms.Form):
    """
    Form for setting new password
    """

    new_password1 = forms.CharField(
        label=_("Nueva contraseña"),
        widget=forms.PasswordInput,
        help_text=_("Ingresa una contraseña segura"),
    )
    new_password2 = forms.CharField(
        label=_("Confirmar nueva contraseña"),
        widget=forms.PasswordInput,
        help_text=_("Ingresa la misma contraseña nuevamente"),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Las contraseñas no coinciden"))

        return cleaned_data
