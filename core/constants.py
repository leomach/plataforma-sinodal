from django.utils.translation import gettext_lazy as _

# Tipos de Usuário
SOCIO = 1
LIDERANCA = 2

TIPO_USUARIO_CHOICES = [
    (SOCIO, _('Sócio')),
    (LIDERANCA, _('Liderança')),
]

# Categorias de Evento
ADMINISTRATIVO = 1
COMUNHAO = 2

CATEGORIA_EVENTO_CHOICES = [
    (ADMINISTRATIVO, _('Administrativo (Congressos, CEs)')),
    (COMUNHAO, _('Comunhão (Acampamentos, Encontros)')),
]

# Papéis no Evento
PAPEL_DELEGADO = 1
PAPEL_EX_OFFICIO = 2
PAPEL_CORRESPONDENTE = 3
PAPEL_VISITANTE = 4

PAPEL_EVENTO_CHOICES = [
    (PAPEL_DELEGADO, _('Delegado (Efetivo)')),
    (PAPEL_EX_OFFICIO, _('Ex-Officio')),
    (PAPEL_CORRESPONDENTE, _('Correspondente')),
    (PAPEL_VISITANTE, _('Visitante')),
]

# Status de Inscrição
STATUS_PENDENTE = 1
STATUS_APROVADO = 2
STATUS_REJEITADO = 3

STATUS_INSCRICAO_CHOICES = [
    (STATUS_PENDENTE, _('Pendente')),
    (STATUS_APROVADO, _('Aprovado')),
    (STATUS_REJEITADO, _('Rejeitado')),
]

# Tipos de Campos Dinâmicos
CAMPO_TEXTO = 1
CAMPO_NUMERO = 2
CAMPO_SELECAO = 3
CAMPO_CHECKBOX = 4

TIPO_CAMPO_CHOICES = [
    (CAMPO_TEXTO, _('Texto')),
    (CAMPO_NUMERO, _('Número')),
    (CAMPO_SELECAO, _('Seleção (Dropdown)')),
    (CAMPO_CHECKBOX, _('Checkbox')),
]
