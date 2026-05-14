from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Evento, CampoEvento, Inscricao, RespostaInscricao
from core import constants


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'titulo', 'descricao', 'categoria', 'data_inicio', 'data_fim',
            'inscricoes_inicio', 'inscricoes_fim', 'local', 'banner', 'vagas',
            'valor_inscricao', 'tipo_financeiro', 'chave_pix', 'instrucoes_pagamento',
            'ativo',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'input-field'}),
            'categoria': forms.Select(attrs={'class': 'input-field bg-white'}),
            'local': forms.TextInput(attrs={'class': 'input-field'}),
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}, format='%Y-%m-%dT%H:%M'),
            'data_fim': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}, format='%Y-%m-%dT%H:%M'),
            'inscricoes_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}, format='%Y-%m-%dT%H:%M'),
            'inscricoes_fim': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input-field'}, format='%Y-%m-%dT%H:%M'),
            'vagas': forms.NumberInput(attrs={'class': 'input-field', 'min': 0, 'placeholder': '0 para ilimitadas'}),
            'valor_inscricao': forms.NumberInput(attrs={'class': 'input-field', 'min': '0', 'step': '0.01', 'id': 'id_valor_inscricao', 'placeholder': '0,00'}),
            'tipo_financeiro': forms.Select(
                choices=[
                    (constants.MANUAL, _('Manual (PIX)')),
                    (constants.INFINITEPAY, _('InfinitePay')),
                ],
                attrs={'class': 'input-field bg-white', 'id': 'id_tipo_financeiro'},
            ),
            'chave_pix': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'CPF, e-mail, telefone ou chave aleatória'}),
            'instrucoes_pagamento': forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': 'Ex: Realize o PIX e envie o comprovante para...'}),
            'descricao': forms.Textarea(attrs={'rows': 5, 'class': 'input-field'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        insc_inicio = cleaned_data.get('inscricoes_inicio')
        insc_fim = cleaned_data.get('inscricoes_fim')
        valor = cleaned_data.get('valor_inscricao') or 0
        tipo = cleaned_data.get('tipo_financeiro', constants.MANUAL)

        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValidationError({'data_fim': 'A data de término não pode ser anterior à data de início.'})

        if insc_inicio and insc_fim and insc_fim < insc_inicio:
            raise ValidationError({'inscricoes_fim': 'O fim das inscrições não pode ser anterior ao início.'})

        if insc_fim and data_fim and insc_fim > data_fim:
            raise ValidationError({'inscricoes_fim': 'O período de inscrição não pode ultrapassar o término do evento.'})

        if valor == 0:
            cleaned_data['tipo_financeiro'] = constants.GRATUITO
        else:
            if tipo == constants.MANUAL and not (cleaned_data.get('chave_pix') or '').strip():
                self.add_error('chave_pix', 'Informe a chave PIX para eventos com pagamento manual.')

        return cleaned_data


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

        self.campos_personalizados = self.evento.campos_personalizados.all()
        
        # Se for edição, busca respostas existentes
        respostas_existentes = {}
        if self.instance and self.instance.pk:
            respostas_existentes = {r.campo_id: r.valor for r in self.instance.respostas.all()}

        for campo in self.campos_personalizados:
            field_key = f'custom_{campo.id}'
            initial_value = respostas_existentes.get(campo.id)

            if campo.tipo_campo == constants.CAMPO_TEXTO:
                self.fields[field_key] = forms.CharField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    initial=initial_value,
                    widget=forms.TextInput(attrs={'class': 'input-field'})
                )
            elif campo.tipo_campo == constants.CAMPO_NUMERO:
                self.fields[field_key] = forms.IntegerField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    initial=initial_value,
                    widget=forms.NumberInput(attrs={'class': 'input-field'})
                )
            elif campo.tipo_campo == constants.CAMPO_SELECAO:
                choices = [(c.strip(), c.strip()) for c in campo.opcoes.split(',') if c.strip()]
                self.fields[field_key] = forms.ChoiceField(
                    label=campo.label,
                    required=campo.obrigatorio,
                    choices=[('', 'Selecione...')] + choices,
                    initial=initial_value,
                    widget=forms.Select(attrs={'class': 'input-field bg-white'})
                )
            elif campo.tipo_campo == constants.CAMPO_CHECKBOX:
                if campo.opcoes:
                    choices = [(c.strip(), c.strip()) for c in campo.opcoes.split(',') if c.strip()]
                    initial_choices = [c.strip() for c in (initial_value or '').split(',')] if initial_value else []
                    self.fields[field_key] = forms.MultipleChoiceField(
                        label=campo.label,
                        required=campo.obrigatorio,
                        choices=choices,
                        initial=initial_choices,
                        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'})
                    )
                else:
                    self.fields[field_key] = forms.BooleanField(
                        label=campo.label,
                        required=campo.obrigatorio,
                        initial=(initial_value == 'True'),
                        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary rounded border-border focus:ring-primary'})
                    )

    def save_custom_fields(self, inscricao):
        for campo in self.campos_personalizados:
            field_key = f'custom_{campo.id}'
            valor = self.cleaned_data.get(field_key)
            if valor is not None:
                if isinstance(valor, list):
                    valor = ', '.join(valor)
                
                RespostaInscricao.objects.update_or_create(
                    inscricao=inscricao,
                    campo=campo,
                    defaults={'valor': str(valor)}
                )
