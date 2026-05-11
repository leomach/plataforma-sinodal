from django import forms
from .models import DocumentoEvento, TipoDocumento

class DocumentoEventoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.Select, forms.NumberInput)):
                field.widget.attrs.update({'class': 'input-field'})

    class Meta:
        model = DocumentoEvento
        fields = ['tipo', 'titulo', 'arquivo_url', 'restrito_delegados', 'ordem']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'input-field'}),
            'titulo': forms.TextInput(attrs={'placeholder': 'Ex: Relatório de Tesouraria 2024'}),
            'arquivo_url': forms.URLInput(attrs={'placeholder': 'https://drive.google.com/...'}),
            'ordem': forms.NumberInput(attrs={'class': 'input-field', 'min': '0'}),
        }

class AtaSessaoRapidaForm(forms.ModelForm):
    """Formulário simplificado para o Secretário lançar a ata rapidamente."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input-field'})

    class Meta:
        model = DocumentoEvento
        fields = ['titulo', 'arquivo_url']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ex: Ata da 2ª Sessão Regular'}),
            'arquivo_url': forms.URLInput(attrs={'placeholder': 'Link do Google Docs'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        tipo_ata = TipoDocumento.objects.filter(nome='Atas/Registro de Atos').first()
        if not tipo_ata:
            tipo_ata = TipoDocumento.objects.create(nome='Atas/Registro de Atos', ordem=8)
        
        instance.tipo = tipo_ata
        instance.is_ata_sessao = True
        instance.restrito_delegados = True
        if commit:
            instance.save()
        return instance
