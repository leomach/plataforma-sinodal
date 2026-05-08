from django import forms
from django.forms import inlineformset_factory
from .models import Evento, CampoEvento, Inscricao, RespostaInscricao
from core import constants

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descricao', 'categoria', 'data_inicio', 'data_fim', 'local', 'banner', 'ativo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'input-field'}),
            'categoria': forms.Select(attrs={'class': 'input-field bg-white'}),
            'local': forms.TextInput(attrs={'class': 'input-field'}),
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}),
            'data_fim': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}),
            'descricao': forms.Textarea(attrs={'rows': 5, 'class': 'input-field'}),
        }

class CampoEventoForm(forms.ModelForm):
    class Meta:
        model = CampoEvento
        fields = ['label', 'tipo_campo', 'obrigatorio', 'opcoes']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Ex: Tamanho da Camisa'}),
            'tipo_campo': forms.Select(attrs={'class': 'input-field bg-white'}),
            'opcoes': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'P, M, G (separados por vírgula)'}),
        }

CampoEventoFormSet = inlineformset_factory(
    Evento, CampoEvento, form=CampoEventoForm,
    extra=1, can_delete=True
)

class InscricaoForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = ['papel_evento', 'credential_url', 'observacoes']
        widgets = {
            'papel_evento': forms.Select(attrs={'class': 'input-field bg-white'}),
            'credential_url': forms.URLInput(attrs={'class': 'input-field', 'placeholder': 'https://drive.google.com/...'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'input-field'}),
        }

    def __init__(self, *args, **kwargs):
        self.evento = kwargs.pop('evento')
        super().__init__(*args, **kwargs)
        
        # Carregar campos dinâmicos
        self.campos_personalizados = self.evento.campos_personalizados.all()
        for campo in self.campos_personalizados:
            field_key = f'custom_{campo.id}'
            
            if campo.tipo_campo == constants.CAMPO_TEXTO:
                self.fields[field_key] = forms.CharField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    widget=forms.TextInput(attrs={'class': 'input-field'})
                )
            elif campo.tipo_campo == constants.CAMPO_NUMERO:
                self.fields[field_key] = forms.IntegerField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    widget=forms.NumberInput(attrs={'class': 'input-field'})
                )
            elif campo.tipo_campo == constants.CAMPO_SELECAO:
                choices = [(c.strip(), c.strip()) for c in campo.opcoes.split(',') if c.strip()]
                self.fields[field_key] = forms.ChoiceField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    choices=[('', 'Selecione...')] + choices,
                    widget=forms.Select(attrs={'class': 'input-field bg-white'})
                )
            elif campo.tipo_campo == constants.CAMPO_CHECKBOX:
                if campo.opcoes:
                    choices = [(c.strip(), c.strip()) for c in campo.opcoes.split(',') if c.strip()]
                    self.fields[field_key] = forms.MultipleChoiceField(
                        label=campo.label,
                        required=campo.obrigatorio,
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'})
                    )
                else:
                    self.fields[field_key] = forms.BooleanField(
                        label=campo.label,
                        required=campo.obrigatorio,
                        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary rounded border-border focus:ring-primary'})
                    )

    def save_custom_fields(self, inscricao):
        for campo in self.campos_personalizados:
            field_key = f'custom_{campo.id}'
            valor = self.cleaned_data.get(field_key)
            if valor is not None:
                # Se for MultipleChoiceField, valor é uma lista
                if isinstance(valor, list):
                    valor = ", ".join(valor)
                RespostaInscricao.objects.create(
                    inscricao=inscricao,
                    campo=campo,
                    valor=str(valor)
                )
