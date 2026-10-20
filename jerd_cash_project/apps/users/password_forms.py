
import re

from django import forms
from django.contrib.auth.forms import SetPasswordForm


class JERDPasswordResetForm(SetPasswordForm):
    """
    Formulario para restablecer la contraseña de un usuario.
    Aplica las reglas de contraseña de JERD-Cash.
    """

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1", "")

        if len(password) < 8:
            raise forms.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "La contraseña debe incluir al menos una letra mayúscula."
            )

        if "." not in password:
            raise forms.ValidationError(
                "La contraseña debe incluir al menos un punto (.)."
            )

        caracteres_especiales = "!@#$%^&*_-+=/?¿¡:;,(){}[]<>|\\'\""

        if not any(c in caracteres_especiales for c in password):
            raise forms.ValidationError(
                "La contraseña debe incluir al menos otro carácter especial."
            )

        return super().clean_new_password1()
