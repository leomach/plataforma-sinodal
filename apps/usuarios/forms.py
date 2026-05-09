from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Sobrenome'), max_length=30, required=True)
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(label=_('Nome'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Sobrenome'), max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'foto', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Conte um pouco sobre você...'}),
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'tipo', 'bio')
