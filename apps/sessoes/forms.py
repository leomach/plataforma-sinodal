from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import MembroDaMesa, Sessao, Votacao, EventoLog

_INPUT_FIELD = 'input-field'


class SessaoForm(forms.ModelForm):
    data_hora = forms.DateTimeField(
        label='Data e Hora',
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': _INPUT_FIELD},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
    )

    class Meta:
        model = Sessao
        fields = ['nome', 'data_hora', 'is_verificacao_poderes']
        labels = {
            'nome': 'Nome da Sessão',
            'is_verificacao_poderes': 'Sessão de Verificação de Poderes',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': _INPUT_FIELD, 'placeholder': 'Ex: 1ª Sessão Ordinária'}),
        }

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        if self.instance.pk and self.instance.data_hora:
            local_dt = timezone.localtime(self.instance.data_hora)
            self.fields['data_hora'].initial = local_dt.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned = super().clean()
        is_vp = cleaned.get('is_verificacao_poderes')
        data_hora = cleaned.get('data_hora')

        if is_vp and self.evento:
            qs = Sessao.objects.filter(evento=self.evento, is_verificacao_poderes=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    'is_verificacao_poderes',
                    'Já existe uma Sessão de Verificação de Poderes para este evento.',
                )

            outras = Sessao.objects.filter(evento=self.evento)
            if self.instance.pk:
                outras = outras.exclude(pk=self.instance.pk)
            if outras.exists() and data_hora:
                minima = outras.order_by('data_hora').first()
                if minima and data_hora > minima.data_hora:
                    self.add_error(
                        'is_verificacao_poderes',
                        'A Sessão de Verificação de Poderes deve ser a primeira do evento (data/hora mais antiga).',
                    )

        return cleaned


class VotacaoForm(forms.ModelForm):
    class Meta:
        model = Votacao
        fields = ['titulo']
        labels = {'titulo': 'Proposta / Título da Votação'}
        widgets = {
            'titulo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descreva a proposta a ser votada...'}),
        }


class EventoLogManualForm(forms.ModelForm):
    class Meta:
        model = EventoLog
        fields = ['descricao']
        labels = {'descricao': 'Registro Manual'}
        widgets = {
            'descricao': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Ex: Oração feita pelo Rev. Carlos Mendes.',
            }),
        }


_SELECT_ATTRS = {
    'class': 'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600/30 focus:border-blue-600 transition-all',
}


class MesaDiretoraForm(forms.Form):
    presidente = forms.ModelChoiceField(
        queryset=None,
        label='Presidente da Mesa',
        empty_label='— Selecione —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    vice_presidente = forms.ModelChoiceField(
        queryset=None,
        label='Vice-Presidente',
        required=False,
        empty_label='— Não designado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    primeiro_secretario = forms.ModelChoiceField(
        queryset=None,
        label='1º Secretário',
        required=False,
        empty_label='— Não designado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    segundo_secretario = forms.ModelChoiceField(
        queryset=None,
        label='2º Secretário',
        required=False,
        empty_label='— Não designado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    tesoureiro = forms.ModelChoiceField(
        queryset=None,
        label='Tesoureiro',
        required=False,
        empty_label='— Não designado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    secretario_executivo = forms.ModelChoiceField(
        queryset=None,
        label='Secretário Executivo',
        required=False,
        empty_label='— Não designado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )
    membros_extras_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='[]',
    )

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.eventos.models import Inscricao
        from core import constants
        qs = Inscricao.objects.filter(
            evento=evento,
            status=constants.STATUS_APROVADO,
        ).select_related('usuario').order_by('usuario__first_name', 'usuario__last_name')
        for field in self.fields.values():
            if hasattr(field, 'queryset'):
                field.queryset = qs
                field.label_from_instance = (
                    lambda insc: insc.usuario.get_full_name() or insc.usuario.username
                )


class OperadorPresencaForm(forms.Form):
    inscricao = forms.ModelChoiceField(
        queryset=None,
        label='Adicionar operador',
        empty_label='— Selecione um inscrito aprovado —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.eventos.models import Inscricao
        from apps.sessoes.models import OperadorPresenca
        from core import constants

        ja_operadores = OperadorPresenca.objects.filter(
            inscricao__evento=evento,
        ).values_list('inscricao_id', flat=True)

        self.fields['inscricao'].queryset = (
            Inscricao.objects.filter(evento=evento, status=constants.STATUS_APROVADO)
            .exclude(pk__in=ja_operadores)
            .select_related('usuario')
            .order_by('usuario__first_name', 'usuario__last_name')
        )
        self.fields['inscricao'].label_from_instance = (
            lambda insc: f"{insc.usuario.get_full_name() or insc.usuario.username} — {insc.get_papel_evento_display()}"
        )


class TransferirPresidenciaForm(forms.Form):
    novo_presidente = forms.ModelChoiceField(
        queryset=None,
        label='Transferir presidência para',
        empty_label='— Selecione —',
        widget=forms.Select(attrs=_SELECT_ATTRS),
    )

    def __init__(self, *args, sessao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['novo_presidente'].queryset = MembroDaMesa.objects.filter(
            sessao=sessao,
            encerrou_em__isnull=True,
        ).exclude(cargo=MembroDaMesa.PRESIDENTE).select_related('inscricao__usuario')
