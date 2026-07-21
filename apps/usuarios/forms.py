import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


def _digitos(valor):
    """Retorna somente os dígitos de uma string."""
    return re.sub(r'\D', '', valor or '')


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Sobrenome Completo'), max_length=30, required=True)
    email = forms.EmailField(
        label=_('E-mail'),
        required=True,
        help_text=_('Usaremos para enviar informações sobre os eventos.'),
    )
    whatsapp = forms.CharField(
        label=_('WhatsApp'),
        max_length=20,
        required=False,
        help_text=_('Inclua o DDD (ex: 11988887777)'),
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000', 'class': 'phone-mask'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'whatsapp')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'duplicate_email',
                code='duplicate_email',
            )
        return email

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp', '').strip()
        if not whatsapp:
            return whatsapp
        digitos = _digitos(whatsapp)
        if len(digitos) >= 8:
            sufixo = digitos[-9:]
            for wa in User.objects.exclude(whatsapp='').values_list('whatsapp', flat=True):
                if _digitos(wa).endswith(sufixo):
                    raise forms.ValidationError(
                        'duplicate_whatsapp',
                        code='duplicate_whatsapp',
                    )
        return whatsapp

class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(
        label=_('Nome de usuário'),
        max_length=150,
        help_text=_('Usado para entrar na plataforma.'),
    )
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Sobrenome Completo'), max_length=30, required=True)
    whatsapp = forms.CharField(
        label=_('WhatsApp'),
        max_length=20,
        required=False,
        help_text=_('Inclua o DDD (ex: 11988887777)'),
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000', 'class': 'phone-mask'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'whatsapp', 'foto', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Conte um pouco sobre você...'}),
        }

class LiderancaUserEditForm(forms.ModelForm):
    """Formulário usado pela liderança para editar os dados de qualquer usuário."""
    username = forms.CharField(
        label=_('Nome de usuário'),
        max_length=150,
        help_text=_('Usado para entrar na plataforma.'),
    )
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=False)
    last_name = forms.CharField(label=_('Sobrenome Completo'), max_length=30, required=False)
    whatsapp = forms.CharField(
        label=_('WhatsApp'),
        max_length=20,
        required=False,
        help_text=_('Inclua o DDD (ex: 11988887777)'),
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000', 'class': 'phone-mask'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'whatsapp')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'tipo', 'bio')
