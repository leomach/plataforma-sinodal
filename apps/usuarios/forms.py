from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Sobrenome Completo'), max_length=30, required=True)
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

class ProfileUpdateForm(forms.ModelForm):
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
        fields = ('first_name', 'last_name', 'email', 'whatsapp', 'foto', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Conte um pouco sobre você...'}),
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'tipo', 'bio')
